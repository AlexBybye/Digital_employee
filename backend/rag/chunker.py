"""Markdown chunker for long-form knowledge docs.

Splits a markdown document into retrieval chunks along heading boundaries,
then further splits any over-long section with an overlapping sliding window
so no single chunk loses semantic coherence or exceeds the embedding budget.

Each chunk carries metadata used by the retriever and the eval harness:
  - source  : doc filename stem (e.g. "account_lifecycle")
  - section : the nearest "##" heading text the chunk belongs to
  - title   : the document "#" title
  - chunk_id: stable id "<source>::<section>#<n>"
  - text    : "section\n\nbody" — what actually gets embedded
"""
import re

# A section that exceeds this many characters is sliding-windowed.
MAX_CHARS = 320
# Overlap between adjacent windows so a sentence split across the boundary
# still appears whole in one of them.
OVERLAP = 60


def _split_long(body: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP) -> list[str]:
    """Sliding-window split on a long body, preferring sentence boundaries."""
    if len(body) <= max_chars:
        return [body]

    # Sentence-ish boundaries for Chinese + ASCII.
    sentences = re.split(r"(?<=[。！？；\n])", body)
    windows: list[str] = []
    cur = ""
    for s in sentences:
        if not s:
            continue
        if len(cur) + len(s) <= max_chars:
            cur += s
        else:
            if cur:
                windows.append(cur.strip())
            # Carry an overlap tail from the previous window for continuity.
            tail = cur[-overlap:] if cur else ""
            cur = tail + s
    if cur.strip():
        windows.append(cur.strip())
    return [w for w in windows if w]


def chunk_markdown(text: str, source: str) -> list[dict]:
    """Chunk one markdown document into a list of chunk dicts.

    Sections are delimited by "##" headings. Text before the first "##" (the
    intro under the "#" title) becomes a "前言" section. Each section body is
    sliding-windowed if it is too long.
    """
    lines = text.splitlines()
    title = ""
    section = "前言"
    buffer: list[str] = []
    sections: list[tuple[str, str]] = []  # (section_name, body)

    def flush():
        body = "\n".join(buffer).strip()
        if body:
            sections.append((section, body))

    for line in lines:
        h1 = re.match(r"^#\s+(.*)", line)
        h2 = re.match(r"^#{2,}\s+(.*)", line)
        if h1:
            title = h1.group(1).strip()
            continue
        if h2:
            flush()
            buffer = []
            section = h2.group(1).strip()
            continue
        buffer.append(line)
    flush()

    chunks: list[dict] = []
    for sec_name, body in sections:
        for i, window in enumerate(_split_long(body)):
            chunks.append({
                "source": source,
                "title": title,
                "section": sec_name,
                "chunk_id": f"{source}::{sec_name}#{i}",
                # Embed the section name with the body so a query about the
                # topic ("密码策略") matches even when the body paraphrases it.
                "text": f"{sec_name}\n\n{window}",
                "body": window,
            })
    return chunks
