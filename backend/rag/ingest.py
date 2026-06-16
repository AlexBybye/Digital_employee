"""Ingest long-form docs from data/docs/*.md into the doc vector store."""
import logging
from pathlib import Path

from rag.chunker import chunk_markdown
from rag.config import DATA_DIR
from rag.doc_store import init_doc_store

logger = logging.getLogger(__name__)

DOCS_DIR = DATA_DIR / "docs"


def load_chunks() -> list[dict]:
    """Read every markdown file under data/docs and chunk it."""
    chunks: list[dict] = []
    if not DOCS_DIR.exists():
        return chunks
    for path in sorted(DOCS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        chunks.extend(chunk_markdown(text, source=path.stem))
    return chunks


def ingest_docs() -> int:
    """Chunk all docs and (re)build the doc vector store. Returns chunk count."""
    chunks = load_chunks()
    init_doc_store(chunks)
    logger.info("Ingested %d doc chunks from %s", len(chunks), DOCS_DIR)
    return len(chunks)
