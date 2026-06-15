"""AI-powered RPA dispatcher.

Takes natural-language commands, uses DeepSeek (via Ollama) to
determine the intended RPA action and parameters, then dispatches
to the corresponding RPA service function.

Security:
- Garbage / nonsensical input is rejected (LLM returns "unknown").
- Dangerous operations on protected accounts (admin) are blocked.
- Password strength is validated.
- All operations have auditable trails via RPA job logs.
"""

import json
import logging
import re

from services.llm_service import _call_ollama
from services.rpa_service import (
    create_account_job,
    freeze_account_job,
    reset_password_job,
    unfreeze_account_job,
)

logger = logging.getLogger(__name__)

# Protected accounts that AI-driven RPA is NOT allowed to touch
_PROTECTED_ACCOUNTS = {"admin", "root", "system", "administrator"}

# Minimum password length for AI-driven operations
_MIN_PASSWORD_LENGTH = 6

_SYSTEM_PROMPT = """将用户指令转为JSON，格式：{"action":"操作名","params":{"参数名":"参数值"}}

操作列表：
reset-password  — 重置密码，参数：username, new_password
create-account  — 创建账号，参数：username, password, full_name, department
freeze-account  — 冻结账号，参数：username, reason
unfreeze-account — 解冻账号，参数：username, reason

无法识别时返回：{"action":"unknown","params":{}}
危险指令（删库、提权、删账号等）返回：{"action":"rejected","params":{}}

示例：
用户：重置ops01的密码为Temp1234
返回：{"action":"reset-password","params":{"username":"ops01","new_password":"Temp1234"}}

用户：创建新账号ops03
返回：{"action":"create-account","params":{"username":"ops03","password":"ops1234","full_name":"新员工","department":"运维部"}}

用户：冻结ops02
返回：{"action":"freeze-account","params":{"username":"ops02","reason":"长期未使用"}}
"""


def _is_nonsense(text: str) -> bool:
    """Quick heuristic check for obviously garbage input."""
    if len(text.strip()) < 4:
        return True
    # Repeated characters like "aaaa", "1111", "。。。"
    if re.fullmatch(r"(.)\1{2,}", text.strip()):
        return True
    return False


def _validate_safety(action: str, params: dict) -> str | None:
    """Validate parameters and return an error message if unsafe, or None if OK."""
    username = params.get("username", "")

    # Block operations on protected accounts
    if username.lower() in _PROTECTED_ACCOUNTS:
        return f"AI 无权操作受保护账号「{username}」，请手动处理"

    # Password strength check
    if action == "reset-password":
        new_pw = params.get("new_password", "")
        if len(new_pw) < _MIN_PASSWORD_LENGTH:
            return f"密码长度不能少于 {_MIN_PASSWORD_LENGTH} 位"
    if action == "create-account":
        new_pw = params.get("password", "")
        if len(new_pw) < _MIN_PASSWORD_LENGTH:
            return f"密码长度不能少于 {_MIN_PASSWORD_LENGTH} 位"

    return None


def parse_intent(user_input: str) -> dict:
    """Use LLM to parse user input into an RPA action and parameters."""
    # Reject obvious garbage before calling LLM
    if _is_nonsense(user_input):
        return {"action": "unknown", "params": {}, "reason": "输入内容无效，请提供明确的运维指令"}

    prompt = f"{_SYSTEM_PROMPT}\n用户：{user_input}\n返回："
    raw = _call_ollama(prompt)
    if not raw:
        return {"action": "unknown", "params": {}, "reason": "AI 模型未响应，请检查 Ollama 服务"}

    # Try to extract JSON from the response — strip markdown fences and extra text
    raw = raw.strip()

    # Remove markdown code fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        if "```" in raw:
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

    # Extract the first JSON object using brace counting (handles nested objects)
    start = raw.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(raw)):
            if raw[i] == "{":
                depth += 1
            elif raw[i] == "}":
                depth -= 1
                if depth == 0:
                    raw = raw[start:i + 1]
                    break

    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict) or "action" not in parsed:
            raise ValueError("Missing action field")
        return parsed
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse LLM intent response: %s", raw)
        return {"action": "unknown", "params": {}, "reason": f"AI 返回格式异常：{raw[:200]}"}


def execute_rpa(command: str) -> dict:
    """Parse a natural-language command and execute the corresponding RPA action.

    Security layers:
    1. Garbage input rejection (heuristic)
    2. LLM-based intent parsing with danger detection
    3. Safety validation (protected accounts, password strength)
    """
    intent = parse_intent(command)
    action = intent.get("action", "unknown")
    params = intent.get("params", {})

    # Layer 1: LLM could not understand or flagged as dangerous
    if action == "unknown":
        reason = intent.get("reason", "无法识别指令")
        return {"success": False, "action": "unknown", "message": reason}

    if action == "rejected":
        reason = intent.get("reason", "危险操作已拦截")
        return {"success": False, "action": "rejected", "message": f"⛔ {reason}"}

    # Layer 2: Safety validation
    safety_error = _validate_safety(action, params)
    if safety_error:
        return {"success": False, "action": action, "message": f"⛔ {safety_error}"}

    # Layer 3: Execute
    try:
        if action == "reset-password":
            result = reset_password_job(
                params["username"], params["new_password"], "ai-agent"
            )
        elif action == "create-account":
            result = create_account_job(
                params.get("username", "new_user"),
                params.get("password", "ops1234"),
                "operator",
                "ai-agent",
                params.get("full_name", ""),
                params.get("department", ""),
            )
        elif action == "freeze-account":
            result = freeze_account_job(
                params["username"], "ai-agent", params.get("reason", "AI 自动化触发")
            )
        elif action == "unfreeze-account":
            result = unfreeze_account_job(
                params["username"], "ai-agent", params.get("reason", "AI 自动化触发")
            )
        else:
            return {"success": False, "action": action, "message": f"不支持的操作：{action}"}

        return {
            "success": result.get("status") == "completed",
            "action": action,
            "message": result.get("result", ""),
            "steps": result.get("steps", []),
            "status": result.get("status"),
        }
    except KeyError as e:
        return {
            "success": False,
            "action": action,
            "message": f"缺少参数：{e}",
        }
    except Exception as e:
        logger.exception("RPA execution failed")
        return {
            "success": False,
            "action": action,
            "message": f"执行异常：{e}",
        }
