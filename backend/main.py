"""FastAPI entrypoint for the Ops Digital Employee backend."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import admin, ai, health, rpa, tickets, users
from database.db import get_faqs, init_database, seed_database
from rag.chroma_store import init_vector_store

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ops Digital Employee API",
    description="Local RAG knowledge base, online reports, ops account maintenance, admin review, and RPA simulation.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(ai.router)
app.include_router(tickets.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(rpa.router)


@app.on_event("startup")
def startup() -> None:
    """Create SQLite tables, seed data, and initialize vector store."""
    init_database()
    seed_database()

    # Initialize ChromaDB vector store for semantic FAQ retrieval
    faqs = get_faqs()
    ready = init_vector_store(faqs)
    if ready:
        logger.info("Vector store initialized with %d FAQs.", len(faqs))
    else:
        logger.warning("Vector store unavailable; using keyword fallback.")
