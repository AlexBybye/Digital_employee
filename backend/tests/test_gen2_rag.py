"""Tests for the Gen-2 chunker and multi-turn query rewriter.

These run offline (no Ollama, no models): the rewriter's rule-based fallback
and the chunker are pure functions. Run from backend/:
    python -m pytest tests/ -v
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from rag.chunker import chunk_markdown, _split_long  # noqa: E402
from rag.query_rewrite import rule_based_rewrite, _needs_context  # noqa: E402


# ---------- chunker ----------

SAMPLE_DOC = """# 测试手册

这是前言段落，位于第一个二级标题之前。

## 第一节

第一节的正文内容，描述某个流程。

## 第二节

第二节的正文内容，描述另一个流程。
"""


def test_chunk_splits_by_heading():
    chunks = chunk_markdown(SAMPLE_DOC, source="manual")
    sections = {c["section"] for c in chunks}
    # Intro (前言) + the two H2 sections.
    assert "前言" in sections
    assert "第一节" in sections
    assert "第二节" in sections


def test_chunk_metadata_shape():
    chunks = chunk_markdown(SAMPLE_DOC, source="manual")
    c = chunks[0]
    for key in ("source", "title", "section", "chunk_id", "text", "body"):
        assert key in c
    assert c["source"] == "manual"
    assert c["title"] == "测试手册"
    # Embedded text includes the section name to aid topical matching.
    assert c["section"] in c["text"]


def test_chunk_ids_unique():
    chunks = chunk_markdown(SAMPLE_DOC, source="manual")
    ids = [c["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids))


def test_split_long_windows_oversized_body():
    body = "。".join([f"这是第{i}个句子内容填充" for i in range(40)])
    windows = _split_long(body, max_chars=120, overlap=20)
    assert len(windows) > 1
    assert all(len(w) <= 120 + 60 for w in windows)  # window + carried overlap


def test_short_body_not_split():
    assert _split_long("短句子。", max_chars=320) == ["短句子。"]


# ---------- query rewrite (rule-based fallback) ----------

def test_needs_context_detects_pronouns_and_ellipsis():
    assert _needs_context("它有有效期吗")          # pronoun 它
    assert _needs_context("那解冻之后多久能用")     # continuation 那
    assert _needs_context("清理完还是高怎么办")     # ellipsis cues
    assert not _needs_context("如何重置运维账号密码")  # self-contained


def test_rewrite_prepends_prior_topic_terms():
    history = [{"role": "user", "text": "账号冻结怎么处理"}]
    out = rule_based_rewrite(history, "那解冻之后多久能用")
    # Carries the prior turn's topic ("账号"/"冻结") into the follow-up.
    assert out != "那解冻之后多久能用"
    assert "账号" in out or "冻结" in out
    assert "那解冻之后多久能用" in out  # original follow-up preserved


def test_rewrite_noop_for_self_contained_query():
    history = [{"role": "user", "text": "账号冻结怎么处理"}]
    out = rule_based_rewrite(history, "如何重置运维账号密码")
    assert out == "如何重置运维账号密码"


def test_rewrite_noop_without_history():
    assert rule_based_rewrite([], "它有有效期吗") == "它有有效期吗"
