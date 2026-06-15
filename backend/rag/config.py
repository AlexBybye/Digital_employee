"""Centralized RAG configuration: model paths, recall/fusion params, routing thresholds.

All magic numbers for the retrieval pipeline live here so the behaviour can be
tuned in one place instead of being scattered across retriever / ai_service.
"""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MODEL_ROOT = DATA_DIR / "models"

# --- Embedding model (bi-encoder, first-stage recall) ---
EMBED_MODEL_DIR = MODEL_ROOT / "bge-small-zh-v1.5"
EMBED_MODEL_NAME = "BAAI/bge-small-zh-v1.5"  # online fallback if local dir missing

# --- Reranker model (cross-encoder, second-stage precision) ---
# Swap to "BAAI/bge-reranker-v2-m3" or a smaller variant by editing these two lines.
RERANKER_MODEL_DIR = MODEL_ROOT / "bge-reranker-base"
RERANKER_MODEL_NAME = "BAAI/bge-reranker-base"  # online fallback if local dir missing

# --- Recall / fusion parameters ---
RECALL_TOP_N = 10   # candidates pulled from EACH channel (vector + BoW) before fusion
RRF_K = 60          # Reciprocal Rank Fusion damping constant (standard default)
RERANK_TOP_K = 5    # how many fused candidates get sent to the cross-encoder
RESULT_LIMIT = 3    # final results returned to the caller

# --- Routing thresholds (applied to the rerank score when available) ---
# The cross-encoder outputs a calibrated relevance score passed through a sigmoid,
# so these absolute values are stable across different knowledge bases.
RERANK_DIRECT = 0.60   # >= -> return FAQ answer directly (no LLM)
RERANK_LLM = 0.20      # [LLM, DIRECT) -> LLM answers with retrieved context
                       # < RERANK_LLM -> create a ticket (human handoff)

# --- Fallback thresholds (applied to the RRF score when reranker is unavailable) ---
# RRF scores are small (sum of 1/(k+rank)); these are calibrated for RRF_K=60
# with two channels, so a doc ranked #1 in both channels scores ~2/61 ≈ 0.0328.
RRF_DIRECT = 0.028
RRF_LLM = 0.012
