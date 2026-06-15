"""Cross-encoder reranker (bge-reranker) for second-stage precision.

Given a query and a list of candidate FAQ entries (already recalled by the
bi-encoder + keyword channels), this scores each (query, document) pair with a
cross-encoder. Cross-encoder scores are calibrated query-document relevance,
so the routing thresholds in config.py stay stable across knowledge bases.

Degrades gracefully: if the model can't be loaded (not downloaded, offline,
sentence-transformers missing), is_ready() returns False and callers fall back
to the RRF fusion score.
"""

import logging

from rag.config import RERANKER_MODEL_DIR, RERANKER_MODEL_NAME

logger = logging.getLogger(__name__)

_reranker = None
_load_attempted = False


def _get_reranker():
    """Lazily load the CrossEncoder once. Returns None if unavailable."""
    global _reranker, _load_attempted
    if _load_attempted:
        return _reranker
    _load_attempted = True
    try:
        from sentence_transformers import CrossEncoder

        if RERANKER_MODEL_DIR.exists():
            logger.info("Loading reranker from local: %s", RERANKER_MODEL_DIR)
            _reranker = CrossEncoder(str(RERANKER_MODEL_DIR), device="cpu")
        else:
            logger.warning(
                "Local reranker not found at %s; trying online download...",
                RERANKER_MODEL_DIR,
            )
            _reranker = CrossEncoder(RERANKER_MODEL_NAME, device="cpu")
    except Exception as exc:  # noqa: BLE001 - any failure means "no reranker"
        logger.warning("Reranker unavailable (%s); falling back to RRF score.", exc)
        _reranker = None
    return _reranker


def is_ready() -> bool:
    """True when the cross-encoder is loaded and usable."""
    return _get_reranker() is not None


def _sigmoid(x: float) -> float:
    # bge-reranker emits raw logits; squash to (0, 1) so thresholds are intuitive.
    import math

    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def rerank(query: str, candidates: list[dict]) -> list[dict]:
    """Attach a ``rerank_score`` to each candidate and sort by it, descending.

    ``candidates`` are dicts containing at least ``question`` and ``answer``.
    Returns a new list sorted by rerank score. If the reranker is unavailable,
    returns the candidates unchanged (caller keeps the upstream RRF ordering).
    """
    model = _get_reranker()
    if model is None or not candidates:
        return candidates

    # Score against question + answer so the cross-encoder sees the full FAQ.
    pairs = [[query, f"{c['question']} {c['answer']}"] for c in candidates]
    try:
        raw_scores = model.predict(pairs)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Rerank prediction failed (%s); keeping RRF order.", exc)
        return candidates

    scored = []
    for cand, raw in zip(candidates, raw_scores):
        scored.append({**cand, "rerank_score": round(_sigmoid(float(raw)), 4)})
    scored.sort(key=lambda x: -x["rerank_score"])
    return scored
