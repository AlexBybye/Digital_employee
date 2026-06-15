"""FAQ retrieval: ChromaDB vector (BGE Chinese) + BoW keyword scores."""
import re
from collections import Counter
from database.db import get_faqs
from rag.chroma_store import is_ready, search as vector_search

TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]+|[a-zA-Z0-9_]+")
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
        if re.fullmatch(r"[\u4e00-\u9fff]+", token):
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

def retrieve(question, limit=3):
    faqs = get_faqs()
    if not faqs: return []

    # Clean noise phrases before matching
    question = clean_query(question)

    # Vector scores (BGE Chinese embedding)
    if is_ready():
        vec_raw = vector_search(question, limit=len(faqs))
        vec_scores = {r["id"]: r["score"] for r in vec_raw}
        worst = min(vec_scores.values()) if vec_scores else 0.0
        for f in faqs: vec_scores.setdefault(f["id"], worst)
    else:
        vec_scores = {f["id"]: 0.0 for f in faqs}

    # BoW scores (question vs question only, with punctuation filter)
    qv = vectorize(question)
    bow_raw = {}
    for faq in faqs:
        bow_raw[faq["id"]] = cosine_similarity(qv, vectorize(faq["question"]))

    # Combined: weighted average (0.7 vec + 0.3 bow)
    results = []
    for faq in faqs:
        fid = faq["id"]
        v = max(0.0, vec_scores.get(fid, 0.0))
        b = max(0.0, bow_raw.get(fid, 0.0))
        combined = 0.7 * v + 0.3 * b
        results.append({**faq, "score": round(combined, 4),
                        "bow_score": round(b, 4), "vec_score": round(v, 4)})

    results.sort(key=lambda x: -x["score"])
    return results[:limit]
