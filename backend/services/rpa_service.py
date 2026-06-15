"""RPA simulation service for account workflows."""

from database.db import create_rpa_job, create_user, get_user_by_username, update_user


def reset_password_job(username: str, new_password: str, requested_by: str) -> dict:
    """Simulate resetting an account password."""
    steps = ["验证请求人", "查找账号", "重置密码", "写入审计记录"]
    user = get_user_by_username(username)
    if user is None:
        result = f"账号 {username} 不存在"
        job_id = create_rpa_job("reset-password", {"username": username, "requested_by": requested_by}, "failed", result)
        return {"job_id": job_id, "action": "reset-password", "status": "failed", "result": result, "steps": steps[:2]}

    update_user(user["id"], {"password": new_password})
    result = f"账号 {username} 密码已重置"
    job_id = create_rpa_job("reset-password", {"username": username, "requested_by": requested_by}, "completed", result)
    return {"job_id": job_id, "action": "reset-password", "status": "completed", "result": result, "steps": steps}


def create_account_job(
    username: str,
    password: str,
    role: str,
    requested_by: str,
    full_name: str = "",
    department: str = "",
    phone: str = "",
    email: str = "",
) -> dict:
    """Simulate creating an ops account."""
    steps = ["验证开户请求", "创建账号", "分配角色", "写入审计记录"]
    try:
        create_user(username, password, role, full_name, department, phone, email, "active")
        status = "completed"
        result = f"账号 {username} 已创建，角色为 {role}"
    except ValueError:
        status = "failed"
        result = f"账号 {username} 已存在"

    job_id = create_rpa_job("create-account", {"username": username, "role": role, "requested_by": requested_by}, status, result)
    return {"job_id": job_id, "action": "create-account", "status": status, "result": result, "steps": steps}


def freeze_account_job(username: str, requested_by: str, reason: str) -> dict:
    """Simulate freezing and cleaning an inactive ops account."""
    steps = ["验证冻结请求", "查询账号状态", "冻结账号", "记录清理原因"]
    user = get_user_by_username(username)
    if user is None:
        result = f"账号 {username} 不存在"
        job_id = create_rpa_job("freeze-account", {"username": username, "requested_by": requested_by}, "failed", result)
        return {"job_id": job_id, "action": "freeze-account", "status": "failed", "result": result, "steps": steps[:2]}

    update_user(user["id"], {"status": "frozen"})
    result = f"账号 {username} 已冻结，原因：{reason}"
    job_id = create_rpa_job(
        "freeze-account",
        {"username": username, "requested_by": requested_by, "reason": reason},
        "completed",
        result,
    )
    return {"job_id": job_id, "action": "freeze-account", "status": "completed", "result": result, "steps": steps}


def unfreeze_account_job(username: str, requested_by: str, reason: str) -> dict:
    """Simulate unfreezing a frozen ops account."""
    steps = ["验证解冻请求", "查询账号状态", "解冻账号", "记录解冻原因"]
    user = get_user_by_username(username)
    if user is None:
        result = f"账号 {username} 不存在"
        job_id = create_rpa_job("unfreeze-account", {"username": username, "requested_by": requested_by}, "failed", result)
        return {"job_id": job_id, "action": "unfreeze-account", "status": "failed", "result": result, "steps": steps[:2]}

    if user["status"] != "frozen":
        result = f"账号 {username} 当前状态为 {user['status']}，无需解冻"
        job_id = create_rpa_job("unfreeze-account", {"username": username, "requested_by": requested_by}, "failed", result)
        return {"job_id": job_id, "action": "unfreeze-account", "status": "failed", "result": result, "steps": steps[:3]}

    update_user(user["id"], {"status": "active"})
    result = f"账号 {username} 已解冻，原因：{reason}"
    job_id = create_rpa_job(
        "unfreeze-account",
        {"username": username, "requested_by": requested_by, "reason": reason},
        "completed",
        result,
    )
    return {"job_id": job_id, "action": "unfreeze-account", "status": "completed", "result": result, "steps": steps}
