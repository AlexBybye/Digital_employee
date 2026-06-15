"""FAQ retrieval pipeline.

Two-stage design:
  1. Recall — pull top-N candidates independently from two channels:
       - vector (BGE Chinese bi-encoder, semantic)
       - BoW    (Chinese tokens + bigrams, lexical)
     Fuse their RANKINGS with Reciprocal Rank Fusion (RRF). RRF is rank-based,
     so it sidesteps the old problem of adding a cosine score (~0.4-0.5 even for
     unrelated text) to a BoW score (0-1) on incomparable scales.
  2. Rerank — a cross-encoder scores each fused candidate against the query.
     This produces a calibrated relevance score the router can threshold on.
     If the reranker is unavailable, the RRF score is used instead.

Each returned result carries:
  - ``score``        : the score the router should use (rerank if available, else lexical BoW)
  - ``score_source`` : "rerank" or "lexical" — tells the router which thresholds apply
  - ``rrf_score`` / ``rerank_score`` / ``bow_score`` / ``vec_rank`` / ``bow_rank`` for transparency
"""
import re
from collections import Counter

from database.db import get_faqs
from rag.chroma_store import is_ready as vector_ready, search as vector_search
from rag.config import RECALL_TOP_N, RRF_K, RERANK_TOP_K, RESULT_LIMIT
from rag.reranker import is_ready as reranker_ready, rerank

TOKEN_PATTERN = re.compile(r"[一-鿿]+|[a-zA-Z0-9_]+")
STOP_WORDS = {"a","an","and","are","can","do","does","for","how","i","in","is","it",
              "of","on","or","should","the","to","user","what","when","with"}
# Punctuation to strip from Chinese text before tokenizing
PUNCTUATION = str.maketrans("", "", "！，。：；“”‘’（）、？）（［］｛｝｝！，。：；""''（）？、＇（）【】｛｝?")

# Common filler / noise phrases that users add but don't appear in FAQ questions
NOISE_PHRASES = [
    r"你好[啊呀吧]?[,，]?$",
    r"我想知道",
    r"我想问一下",
    r"请问一下",
    r"请问",
    r"帮我[看查]一下",
    r"帮我看[看下]",
    r"应该怎么(?:做|办|处理|解决)",
    r"怎么(?:做|办|处理|解决)[呢啊]?$",
    r"了[呢啊]?$",
    r"呢[?？]?$",
    r"吗[?？]?$",
]
NOISE_RE = re.compile("|".join(NOISE_PHRASES))


def clean_query(text: str) -> str:
    """Remove common noise phrases from user queries to improve FAQ matching."""
    text = NOISE_RE.sub("", text).strip()
    # Remove leading "我的"/"你们的" etc.
    text = re.sub(r"^[我你你们]的", "", text).strip()
    return text


def tokens(text):
    text = text.translate(PUNCTUATION)
    result = []
    for token in TOKEN_PATTERN.findall(text.lower()):
        if token in STOP_WORDS: continue
        if re.fullmatch(r"[一-鿿]+", token):
            result.extend(token)
            result.extend(token[i:i+2] for i in range(len(token)-1))
        else:
            result.append(token)
    return result


def vectorize(text):
    return Counter(tokens(text))


def cosine_similarity(left, right):
    if not left or not right: return 0.0
    common = set(left) & set(right)
    num = sum(left[t] * right[t] for t in common)
    ln = sum(v*v for v in left.values())**0.5
    rn = sum(v*v for v in right.values())**0.5
    return num/(ln*rn) if ln and rn else 0.0


def _vector_ranking(question, faqs):
    """Return faq_ids ordered best-first by vector similarity (empty if offline)."""
    if not vector_ready():
        return []
    raw = vector_search(question, limit=min(RECALL_TOP_N, len(faqs)))
    return [r["id"] for r in raw]


def _bow_ranking(question, faqs):
    """Return (ordered faq_ids, {id: bow_score}) by keyword cosine similarity."""
    qv = vectorize(question)
    scored = [(f["id"], cosine_similarity(qv, vectorize(f["question"]))) for f in faqs]
    scored.sort(key=lambda x: -x[1])
    ordered = [fid for fid, score in scored[:RECALL_TOP_N] if score > 0]
    return ordered, {fid: score for fid, score in scored}


def _rrf_fuse(*rankings):
    """Reciprocal Rank Fusion: score = Σ 1/(RRF_K + rank). Rank-based, scale-free."""
    fused = {}
    for ranking in rankings:
        for rank, fid in enumerate(ranking):  # rank starts at 0
            fused[fid] = fused.get(fid, 0.0) + 1.0 / (RRF_K + rank + 1)
    return fused


def retrieve(question, limit=RESULT_LIMIT):
    """Run the full recall → fuse → rerank pipeline and return ranked FAQs."""
    faqs = get_faqs()
    if not faqs:
        return []

    question = clean_query(question)
    faq_by_id = {f["id"]: f for f in faqs}

    # --- Stage 1: dual-channel recall + RRF fusion ---
    vec_rank = _vector_ranking(question, faqs)
    bow_rank, bow_scores = _bow_ranking(question, faqs)
    vec_pos = {fid: i for i, fid in enumerate(vec_rank)}
    bow_pos = {fid: i for i, fid in enumerate(bow_rank)}

    fused = _rrf_fuse(vec_rank, bow_rank)
    if not fused:
        return []

    fused_ids = sorted(fused, key=lambda fid: -fused[fid])

    candidates = []
    for fid in fused_ids[:RERANK_TOP_K]:
        faq = faq_by_id[fid]
        candidates.append({
            **faq,
            "rrf_score": round(fused[fid], 4),
            "bow_score": round(bow_scores.get(fid, 0.0), 4),
            "vec_rank": vec_pos.get(fid, -1),
            "bow_rank": bow_pos.get(fid, -1),
        })

    # --- Stage 2: cross-encoder rerank (with graceful fallback) ---
    # RRF gave us a good candidate ORDERING; routing now needs a magnitude-aware
    # score. Use the calibrated reranker score when the model is loaded, else the
    # lexical (BoW) cosine — both discriminate strong vs weak matches, unlike RRF.
    if reranker_ready():
        candidates = rerank(question, candidates)
        for c in candidates:
            c["score"] = c.get("rerank_score", 0.0)
            c["score_source"] = "rerank"
    else:
        # Re-sort by lexical score so the routing-relevant signal also drives order.
        candidates.sort(key=lambda c: -c["bow_score"])
        for c in candidates:
            c["score"] = c["bow_score"]
            c["score_source"] = "lexical"

    return candidates[:limit]
