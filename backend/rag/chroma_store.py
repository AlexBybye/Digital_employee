"""Lightweight vector store using numpy + BGE embeddings (no chromadb)."""
import logging
import os
import pickle
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MODEL_DIR = DATA_DIR / "models" / "bge-small-zh-v1.5"
VECTOR_CACHE = DATA_DIR / "vectors.pkl"

_encoder = None
_vector_cache = None  # {faq_id: {"vector": np.array, "question": str, "answer": str}}


def _get_encoder():
    global _encoder
    if _encoder is None:
        from sentence_transformers import SentenceTransformer
        # Load from local model directory (bundled with project, no network needed)
        if MODEL_DIR.exists():
            logger.info("Loading BGE-small-zh-v1.5 from local: %s", MODEL_DIR)
            _encoder = SentenceTransformer(str(MODEL_DIR), device="cpu")
        else:
            logger.warning("Local model not found at %s, trying online download...", MODEL_DIR)
            _encoder = SentenceTransformer("BAAI/bge-small-zh-v1.5", device="cpu")
    return _encoder


def _embed(text: str) -> np.ndarray:
    return _get_encoder().encode(text)


def _embed_batch(texts: list[str]) -> list[np.ndarray]:
    return _get_encoder().encode(texts)


def init_vector_store(faqs=None) -> bool:
    global _vector_cache
    try:
        _vector_cache = {}
        if faqs:
            texts = [f"{f['question']} {f['answer']}" for f in faqs]
            vectors = _embed_batch(texts)
            for i, faq in enumerate(faqs):
                _vector_cache[faq["id"]] = {
                    "vector": vectors[i],
                    "question": faq["question"],
                    "answer": faq["answer"],
                }
            # Cache to disk
            with open(VECTOR_CACHE, "wb") as f:
                pickle.dump(_vector_cache, f)
            logger.info("Vector store ready: %d FAQs indexed.", len(faqs))
        return True
    except Exception as exc:
        logger.warning("Vector store offline (%s); using keyword fallback.", exc)
        _vector_cache = None
        return False


def sync_to_vector_store(faqs) -> None:
    """Rebuild the vector index from scratch."""
    init_vector_store(faqs)


def search(query: str, limit: int = 3) -> list[dict]:
    """Brute-force cosine similarity search over all cached vectors."""
    if _vector_cache is None or not _vector_cache:
        return []
    qv = _embed(query)
    results = []
    for fid, data in _vector_cache.items():
        vec = data["vector"]
        cos = float(np.dot(qv, vec) / (np.linalg.norm(qv) * np.linalg.norm(vec)))
        results.append({
            "id": fid,
            "question": data["question"],
            "answer": data["answer"],
            "tags": [],
            "score": round(cos, 4),
        })
    results.sort(key=lambda x: -x["score"])
    return results[:limit]


def is_ready() -> bool:
    return _vector_cache is not None
