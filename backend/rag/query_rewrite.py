"""Multi-turn query rewriting: turn a context-dependent follow-up into a
self-contained query before retrieval.

Two strategies, in priority order:
  1. LLM (Ollama) — best quality; rewrites using full conversation context.
  2. Rule-based fallback — runs OFFLINE (no Ollama). Detects context-dependent
     follow-ups (pronouns / ellipsis / topic-continuation cues) and prepends the
     salient topic terms from the previous user turn.

The fallback exists so the eval harness produces reproducible multi-turn numbers
without a running LLM. When Ollama IS available the LLM path takes over and is
typically better; the report records which path was used.
"""
import re

from services.llm_service import call_ollama

# Cues that a follow-up cannot stand on its own and needs prior context.
_PRONOUN_CUES = ["它", "他", "她", "这个", "那个", "这些", "那些", "此", "该", "这", "那"]
_ELLIPSIS_CUES = ["呢", "的呢", "怎么办", "还能", "还是", "之后", "完", "吗", "有什么", "进"]
_TOPIC_CONTINUATION = ["那", "如果", "要是", "万一"]

# Topic keywords worth carrying forward from the previous turn (ops domain).
_TOPIC_TERMS = [
    "账号", "密码", "冻结", "解冻", "注销", "创建", "重置",
    "VPN", "磁盘", "CPU", "内存", "网络", "服务器", "告警",
    "工单", "知识库", "RPA", "进程", "登录", "AI", "回答", "申告",
]


def _needs_context(follow_up: str) -> bool:
    """Heuristic: does this follow-up depend on prior turns?"""
    if any(p in follow_up for p in _PRONOUN_CUES):
        return True
    if any(follow_up.startswith(t) for t in _TOPIC_CONTINUATION):
        return True
    # Short follow-ups ending in an ellipsis cue are almost always continuations
    # ("清理完还是高怎么办", "那CPU高的呢", "处理完的结果会进知识库吗").
    if len(follow_up) <= 16 and any(c in follow_up for c in _ELLIPSIS_CUES):
        return True
    return False


def _topic_terms(text: str) -> list[str]:
    """Salient ops topic terms present in a piece of text, in first-seen order."""
    found = []
    for term in _TOPIC_TERMS:
        if term in text and term not in found:
            found.append(term)
    return found


def _last_user_turn(history: list[dict]) -> str:
    for turn in reversed(history or []):
        if turn.get("role") == "user" and turn.get("text"):
            return turn["text"]
    return ""


def rule_based_rewrite(history: list[dict], follow_up: str) -> str:
    """Offline rewrite: prepend prior-turn topic terms when the follow-up needs them."""
    if not history or not _needs_context(follow_up):
        return follow_up

    prev = _last_user_turn(history)
    prev_terms = _topic_terms(prev)
    if not prev_terms:
        return follow_up

    # Don't duplicate terms already present in the follow-up itself.
    carry = [t for t in prev_terms if t not in follow_up]
    if not carry:
        return follow_up

    # "账号 解冻 那解冻之后多久能用" — keep the follow-up intact, just prefix context.
    return f"{' '.join(carry)} {follow_up}"


_LLM_PROMPT = (
    "你是查询改写助手。根据对话历史，把用户最新的追问改写成一个不依赖上下文、"
    "可独立检索的完整问题。只输出改写后的问题本身，不要解释。\n\n"
    "对话历史：\n{history}\n\n最新追问：{follow_up}\n\n改写后的问题："
)


def llm_rewrite(history: list[dict], follow_up: str) -> str | None:
    """Ollama-based rewrite. Returns None when Ollama is unavailable."""
    hist_text = "\n".join(
        f"{t.get('role', 'user')}: {t.get('text', '')}" for t in (history or [])
    )
    out = call_ollama(_LLM_PROMPT.format(history=hist_text, follow_up=follow_up), max_tokens=128)
    if not out:
        return None
    # Strip any chain-of-thought / quoting the small model may add.
    out = re.sub(r"<think>.*?</think>", "", out, flags=re.DOTALL).strip()
    out = out.splitlines()[0].strip().strip("「」\"'") if out else ""
    return out or None


def rewrite_query(history: list[dict], follow_up: str, prefer_llm: bool = True) -> str:
    """Rewrite a follow-up into a self-contained query (LLM first, rule fallback)."""
    if prefer_llm:
        rewritten = llm_rewrite(history, follow_up)
        if rewritten:
            return rewritten
    return rule_based_rewrite(history, follow_up)
