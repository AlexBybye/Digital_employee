"""Ollama local LLM adapter.

Connects to a locally running Ollama instance (http://localhost:11434)
to generate real AI answers powered by DeepSeek / Qwen and other
open-source models.

Falls back to a placeholder message when Ollama is unreachable, so the
application can still function for demo purposes.
"""

import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "deepseek-r1:1.5b"
OLLAMA_TIMEOUT = 60  # seconds


def _call_ollama(prompt: str) -> str | None:
    """Send a prompt to Ollama and return the generated text.

    Returns ``None`` if the request fails (Ollama not running, model
    not pulled, network error, etc.).
    """
    return call_ollama(prompt)


def call_ollama(prompt: str, max_tokens: int = 1024) -> str | None:
    """Public Ollama call, reusable by other modules (e.g. query rewrite)."""
    payload = json.dumps(
        {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.15, "top_p": 0.7, "max_tokens": max_tokens},
        }
    ).encode()

    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as resp:
            result = json.loads(resp.read().decode())
            return result.get("response", "").strip()
    except urllib.error.URLError as exc:
        logger.warning("Ollama not reachable (%s); using fallback.", exc)
    except json.JSONDecodeError as exc:
        logger.warning("Invalid JSON from Ollama (%s); using fallback.", exc)
    except Exception as exc:
        logger.warning("Unexpected error calling Ollama (%s); using fallback.", exc)
    return None


def _build_prompt(question: str, sources: list[dict]) -> str:
    """Build a RAG prompt that includes the retrieved FAQ entries.

    Only sources with score >= 50% of the top score are included,
    to avoid injecting irrelevant context into the LLM.
    """
    if not sources:
        return (
            f"知识库中没有相关信息。请直接告知用户无法回答此问题，"
            f"并建议联系运维人员处理。\n\n用户问题：{question}"
        )

    top_score = sources[0].get("score", 0)
    threshold = max(top_score * 0.75, 0.30)
    relevant = [s for s in sources if s.get("score", 0) >= threshold]

    if not relevant:
        return (
            f"知识库中没有相关信息。请直接告知用户无法回答此问题，"
            f"并建议联系运维人员处理。\n\n用户问题：{question}"
        )

    context_parts = []
    for i, src in enumerate(relevant, 1):
        context_parts.append(f"[{i}] 问题：{src['question']}\n    答案：{src['answer']}")
    context = "\n\n".join(context_parts)

    return (
        f"你是一个运维问答助手。根据下面资料回答问题。\n"
        f"注意：如果资料与问题无关，直接回复『知识库中没有相关信息』\n"
        f"不要编造资料中没有的内容。\n\n"
        f"资料：\n{context}\n\n"
        f"问题：{question}"
    )


def generate_answer(question: str, sources: list[dict]) -> str:
    """Generate an answer via Ollama (DeepSeek), with FAQ sources as context."""
    prompt = _build_prompt(question, sources)
    answer = _call_ollama(prompt)

    if answer:
        return answer

    # Fallback when Ollama is not available
    if not sources:
        return "知识库暂时没有足够信息回答该问题，系统已自动创建工单等待管理员处理。"
    best = sources[0]
    return f"根据私有知识库 FAQ #{best['id']}：{best['answer']}"
