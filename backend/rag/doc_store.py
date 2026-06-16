"""Vector store for long-form doc chunks (parallel to the FAQ store).

Kept separate from chroma_store so the FAQ retrieval path stays untouched.
Reuses the same BGE encoder. Chunks are assigned synthetic int ids (offset by
DOC_ID_BASE) so they satisfy the same RagSource schema as FAQs and flow through
the existing rerank/routing code unchanged, while also carrying source/section
metadata for citation and evaluation.
"""
import logging

import numpy as np

from rag.chroma_store import _embed, _embed_batch  # reuse the loaded encoder

logger = logging.getLogger(__name__)

# Synthetic id space for doc chunks, disjoint from FAQ ids (which start at 1).
DOC_ID_BASE = 100_000

_doc_cache = None  # {synthetic_id: {vector, source, section, title, body, chunk_id}}


def init_doc_store(chunks: list[dict]) -> bool:
    """Embed and cache doc chunks. Returns True on success (or empty input)."""
    global _doc_cache
    try:
        _doc_cache = {}
        if chunks:
            vectors = _embed_batch([c["text"] for c in chunks])
            for i, c in enumerate(chunks):
                _doc_cache[DOC_ID_BASE + i] = {
                    "vector": vectors[i],
                    "source": c["source"],
                    "section": c["section"],
                    "title": c.get("title", ""),
                    "body": c["body"],
                    "chunk_id": c["chunk_id"],
                }
            logger.info("Doc store ready: %d chunks indexed.", len(chunks))
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Doc store offline (%s); docs will be skipped.", exc)
        _doc_cache = None
        return False


def doc_search(query: str, limit: int = 5) -> list[dict]:
    """Brute-force cosine search over doc chunks; FAQ-shaped result dicts."""
    if not _doc_cache:
        return []
    qv = _embed(query)
    qn = np.linalg.norm(qv)
    results = []
    for sid, data in _doc_cache.items():
        vec = data["vector"]
        denom = qn * np.linalg.norm(vec)
        cos = float(np.dot(qv, vec) / denom) if denom else 0.0
        results.append({
            "id": sid,
            "question": data["section"],   # section acts as the chunk's "question"
            "answer": data["body"],
            "tags": [data["source"], data["section"]],
            "source": data["source"],
            "section": data["section"],
            "title": data["title"],
            "chunk_id": data["chunk_id"],
            "score": round(cos, 4),
        })
    results.sort(key=lambda x: -x["score"])
    return results[:limit]


def doc_payload(sid: int) -> dict | None:
    """Return the full cached payload for a synthetic doc id (for BoW/candidate build)."""
    if not _doc_cache:
        return None
    return _doc_cache.get(sid)


def all_docs() -> list[dict]:
    """Return all cached doc chunks as FAQ-shaped dicts (id + section + body + meta)."""
    if not _doc_cache:
        return []
    return [
        {
            "id": sid,
            "question": d["section"],
            "answer": d["body"],
            "tags": [d["source"], d["section"]],
            "source": d["source"],
            "section": d["section"],
            "title": d["title"],
            "chunk_id": d["chunk_id"],
        }
        for sid, d in _doc_cache.items()
    ]


def is_ready() -> bool:
    return _doc_cache is not None and len(_doc_cache) > 0
