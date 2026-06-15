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

# NOTE on the scoring contract:
#   RRF is used ONLY to ORDER the recall set (combine the vector + BoW rankings
#   so the best candidates reach the reranker). RRF scores are rank-based — the
#   top item is always ~1/(RRF_K+1) regardless of match strength — so they are
#   NEVER used as a routing confidence. Routing always keys off a magnitude-aware
#   score: the calibrated reranker score when available, else the lexical (BoW)
#   cosine, which is 0 for no overlap and discriminates strong vs weak matches.

# --- Routing thresholds: reranker online (calibrated cross-encoder score) ---
RERANK_DIRECT = 0.60   # >= -> return FAQ answer directly (no LLM)
RERANK_LLM = 0.20      # [LLM, DIRECT) -> LLM answers with retrieved context
                       # < RERANK_LLM -> create a ticket (human handoff)

# --- Routing thresholds: reranker offline (lexical BoW cosine, 0..1) ---
# Calibrated against the FAQ set: a near-verbatim question scores ~0.6-0.7,
# a loosely related one ~0.1-0.3, an off-topic query ~0.0-0.05.
LEX_DIRECT = 0.45      # strong lexical overlap -> direct FAQ answer
LEX_LLM = 0.12         # some overlap -> LLM with context; below -> ticket

