"""Data layer for SQLite tickets/users and JSON FAQ knowledge base."""

import hashlib
import json
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "tickets.db"
FAQ_PATH = DATA_DIR / "faq.json"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'operator',
    full_name TEXT NOT NULL DEFAULT '',
    department TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    email TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    user TEXT NOT NULL,
    contact TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'general',
    priority TEXT NOT NULL DEFAULT 'normal',
    status TEXT NOT NULL DEFAULT 'open',
    answer TEXT,
    resolver TEXT,
    callback_status TEXT NOT NULL DEFAULT 'pending',
    callback_note TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS rpa_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL,
    result TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


USER_MIGRATIONS = {
    "full_name": "TEXT NOT NULL DEFAULT ''",
    "department": "TEXT NOT NULL DEFAULT ''",
    "phone": "TEXT NOT NULL DEFAULT ''",
    "email": "TEXT NOT NULL DEFAULT ''",
    "status": "TEXT NOT NULL DEFAULT 'active'",
}

TICKET_MIGRATIONS = {
    "contact": "TEXT NOT NULL DEFAULT ''",
    "category": "TEXT NOT NULL DEFAULT 'general'",
    "priority": "TEXT NOT NULL DEFAULT 'normal'",
    "callback_status": "TEXT NOT NULL DEFAULT 'pending'",
    "callback_note": "TEXT",
}


def hash_password(password: str) -> str:
    """Hash a password for demo account storage."""
    salt = secrets.token_hex(16)
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password for the lightweight login demo."""
    try:
        salt, expected_digest = stored_hash.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return secrets.compare_digest(digest, expected_digest)


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """Convert a SQLite row into a plain dictionary."""
    if row is None:
        return None
    return dict(row)


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection and commit or rollback safely."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_columns(conn: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    """Apply additive SQLite migrations for existing local databases."""
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    for column, definition in columns.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_database() -> None:
    """Create SQLite tables, apply small migrations, and ensure FAQ file exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with connection() as conn:
        conn.executescript(SCHEMA_SQL)
        _ensure_columns(conn, "users", USER_MIGRATIONS)
        _ensure_columns(conn, "tickets", TICKET_MIGRATIONS)
    if not FAQ_PATH.exists():
        save_faqs(default_faqs())


def seed_database() -> None:
    """Insert or enrich demo users and a sample ticket once."""
    demo_users = [
        ("admin", "admin", "admin", "系统管理员", "运维管理部", "13300000001", "admin@example.com"),
        ("ops01", "ops1234", "operator", "一线运维员", "基础设施组", "13300000002", "ops01@example.com"),
        ("viewer01", "viewer123", "viewer", "只读观察员", "服务台", "13300000003", "viewer01@example.com"),
    ]

    with connection() as conn:
        user_total = conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()["total"]
        if user_total == 0:
            for username, password, role, full_name, department, phone, email in demo_users:
                conn.execute(
                    """
                    INSERT INTO users
                        (username, password_hash, role, full_name, department, phone, email, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
                    """,
                    (username, hash_password(password), role, full_name, department, phone, email),
                )
        else:
            for username, password, role, full_name, department, phone, email in demo_users:
                conn.execute(
                    """
                    UPDATE users
                    SET role = COALESCE(NULLIF(role, ''), ?),
                        full_name = COALESCE(NULLIF(full_name, ''), ?),
                        department = COALESCE(NULLIF(department, ''), ?),
                        phone = COALESCE(NULLIF(phone, ''), ?),
                        email = COALESCE(NULLIF(email, ''), ?),
                        status = COALESCE(NULLIF(status, ''), 'active')
                    WHERE username = ?
                    """,
                    (role, full_name, department, phone, email, username),
                )
                row = conn.execute("SELECT password_hash FROM users WHERE username = ?", (username,)).fetchone()
                if row is not None and "$" not in row["password_hash"]:
                    conn.execute(
                        "UPDATE users SET password_hash = ? WHERE username = ?",
                        (hash_password(password), username),
                    )

        ticket_total = conn.execute("SELECT COUNT(*) AS total FROM tickets").fetchone()["total"]
        if ticket_total == 0:
            conn.execute(
                """
                INSERT INTO tickets
                    (question, user, contact, category, priority, status, callback_status)
                VALUES (?, ?, ?, ?, ?, 'open', 'pending')
                """,
                ("账号冻结后如何恢复？", "ops01", "13300000002", "account", "normal"),
            )


def default_faqs() -> list[dict]:
    """Return starter FAQ records for the private ops knowledge base."""
    return [
        {
            "id": 1,
            "question": "账号冻结怎么处理？",
            "answer": "通过自助门户访问 http://XXX.YYY.ZZZ 提交解冻申请，或拨打运维热线 XXXXX；管理员核验身份后可在账号管理中解冻。",
            "tags": ["账号", "冻结", "自助服务"],
        },
        {
            "id": 2,
            "question": "如何重置运维账号密码？",
            "answer": "在 RPA 模拟功能中执行 reset-password 流程，输入账号和临时密码，系统会记录自动化审计日志。",
            "tags": ["账号", "密码", "RPA"],
        },
        {
            "id": 3,
            "question": "如何创建新的运维人员账号？",
            "answer": "后台账号维护中新增账号，填写用户名、初始密码、角色、姓名、部门、电话和邮箱；也可以调用 create-account RPA 流程。",
            "tags": ["账号", "新增", "后台维护"],
        },
        {
            "id": 4,
            "question": "AI 无法回答时怎么办？",
            "answer": "系统会自动生成在线申告记录，后台运维人员处理并回访，处理结果可自动沉淀到 FAQ 知识库。",
            "tags": ["工单", "人工处理", "自学习"],
        },
        {
            "id": 5,
            "question": "服务器磁盘空间告警怎么处理？",
            "answer": "先确认告警主机和挂载点，清理临时文件和过期日志；若使用率仍高于 85%，升级给二线运维扩容。",
            "tags": ["服务器", "告警", "磁盘"],
        },
        {
            "id": 6,
            "question": "VPN 无法登录怎么处理？",
            "answer": "检查账号状态、密码是否过期、客户端版本和网络连通性；若账号冻结，先走账号解冻流程。",
            "tags": ["VPN", "账号", "网络"],
        },
    ]


def reset_faqs() -> list[dict]:
    """Reset the FAQ file to starter records for demos."""
    faqs = default_faqs()
    save_faqs(faqs)
    return faqs


def get_faqs() -> list[dict]:
    """Load FAQ records from data/faq.json."""
    if not FAQ_PATH.exists():
        save_faqs(default_faqs())
    return json.loads(FAQ_PATH.read_text(encoding="utf-8"))


def save_faqs(faqs: list[dict]) -> None:
    """Persist FAQ records to data/faq.json."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FAQ_PATH.write_text(json.dumps(faqs, ensure_ascii=False, indent=2), encoding="utf-8")


def add_faq(question: str, answer: str, tags: list[str] | None = None) -> dict:
    """Append a new FAQ record and sync to vector store."""
    faqs = get_faqs()
    next_id = max((item["id"] for item in faqs), default=0) + 1
    faq = {"id": next_id, "question": question, "answer": answer, "tags": tags or []}
    faqs.append(faq)
    save_faqs(faqs)
    _try_sync_vector(faqs)
    return faq


def update_faq(faq_id: int, values: dict) -> dict | None:
    """Update a FAQ record by id and sync to vector store."""
    faqs = get_faqs()
    for item in faqs:
        if item["id"] == faq_id:
            item.update(values)
            save_faqs(faqs)
            _try_sync_vector(faqs)
            return item
    return None


def delete_faq(faq_id: int) -> bool:
    """Delete a FAQ record by id and sync to vector store."""
    faqs = get_faqs()
    remaining = [item for item in faqs if item["id"] != faq_id]
    if len(remaining) == len(faqs):
        return False
    save_faqs(remaining)
    _try_sync_vector(remaining)
    return True


def _try_sync_vector(faqs: list[dict]) -> None:
    """Sync FAQ data to the ChromaDB vector store if available."""
    try:
        from rag.chroma_store import sync_to_vector_store
        sync_to_vector_store(faqs)
    except Exception:
        pass  # vector store not available, silently ignore


def list_tickets(status: str | None = None, keyword: str | None = None,
                  user: str | None = None) -> list[dict]:
    """Return tickets from SQLite, with optional status, keyword, and user filtering."""
    sql = "SELECT * FROM tickets WHERE 1 = 1"
    params: list[str] = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if keyword:
        sql += " AND (question LIKE ? OR user LIKE ? OR category LIKE ?)"
        pattern = f"%{keyword}%"
        params.extend([pattern, pattern, pattern])
    if user:
        sql += " AND user = ?"
        params.append(user)
    sql += " ORDER BY id DESC"

    with connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


def get_ticket(ticket_id: int) -> dict | None:
    """Return one ticket."""
    with connection() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        return row_to_dict(row)


def create_ticket(
    question: str,
    user: str,
    contact: str = "",
    category: str = "general",
    priority: str = "normal",
) -> dict:
    """Create a new online report ticket."""
    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tickets
                (question, user, contact, category, priority, status, callback_status)
            VALUES (?, ?, ?, ?, ?, 'open', 'pending')
            """,
            (question, user, contact, category, priority),
        )
        ticket_id = cursor.lastrowid
    return get_ticket(int(ticket_id))


def update_ticket(ticket_id: int, values: dict) -> dict | None:
    """Patch ticket fields."""
    ticket = get_ticket(ticket_id)
    if ticket is None:
        return None

    status = values.get("status", ticket["status"])
    answer = values.get("answer", ticket["answer"])
    resolver = values.get("resolver", ticket["resolver"])
    contact = values.get("contact", ticket["contact"])
    category = values.get("category", ticket["category"])
    priority = values.get("priority", ticket["priority"])
    callback_status = values.get("callback_status", ticket["callback_status"])
    callback_note = values.get("callback_note", ticket["callback_note"])
    resolved_at_sql = "CURRENT_TIMESTAMP" if status == "resolved" else "resolved_at"

    with connection() as conn:
        conn.execute(
            f"""
            UPDATE tickets
            SET status = ?, answer = ?, resolver = ?, contact = ?, category = ?,
                priority = ?, callback_status = ?, callback_note = ?,
                updated_at = CURRENT_TIMESTAMP,
                resolved_at = {resolved_at_sql}
            WHERE id = ?
            """,
            (
                status,
                answer,
                resolver,
                contact,
                category,
                priority,
                callback_status,
                callback_note,
                ticket_id,
            ),
        )
    return get_ticket(ticket_id)


def public_user(row: dict | None) -> dict | None:
    """Remove password hash from a user record."""
    if row is None:
        return None
    row.pop("password_hash", None)
    return row


def list_users(
    keyword: str | None = None,
    role: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """Return ops users with optional query filters."""
    sql = "SELECT * FROM users WHERE 1 = 1"
    params: list[str] = []
    if keyword:
        sql += " AND (username LIKE ? OR full_name LIKE ? OR department LIKE ? OR phone LIKE ?)"
        pattern = f"%{keyword}%"
        params.extend([pattern, pattern, pattern, pattern])
    if role:
        sql += " AND role = ?"
        params.append(role)
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY id DESC"

    with connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [public_user(dict(row)) for row in rows]


def get_user(user_id: int) -> dict | None:
    """Return one public user record."""
    with connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return public_user(row_to_dict(row))


def get_user_by_username(username: str) -> dict | None:
    """Return an internal user record by username."""
    with connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return row_to_dict(row)


def create_user(
    username: str,
    password: str,
    role: str,
    full_name: str = "",
    department: str = "",
    phone: str = "",
    email: str = "",
    status: str = "active",
) -> dict:
    """Create an ops user with identity information."""
    try:
        with connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users
                    (username, password_hash, role, full_name, department, phone, email, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (username, hash_password(password), role, full_name, department, phone, email, status),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError as exc:
        raise ValueError("username already exists") from exc
    return get_user(int(user_id))


def update_user(user_id: int, values: dict) -> dict | None:
    """Patch an ops user."""
    current = get_user_by_id_internal(user_id)
    if current is None:
        return None

    username = values.get("username", current["username"])
    role = values.get("role", current["role"])
    full_name = values.get("full_name", current["full_name"])
    department = values.get("department", current["department"])
    phone = values.get("phone", current["phone"])
    email = values.get("email", current["email"])
    status = values.get("status", current["status"])
    password_hash = hash_password(values["password"]) if values.get("password") else current["password_hash"]

    try:
        with connection() as conn:
            conn.execute(
                """
                UPDATE users
                SET username = ?, password_hash = ?, role = ?, full_name = ?,
                    department = ?, phone = ?, email = ?, status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (username, password_hash, role, full_name, department, phone, email, status, user_id),
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError("username already exists") from exc
    return get_user(user_id)


def freeze_user(user_id: int, status: str) -> dict | None:
    """Freeze or reactivate an ops account."""
    return update_user(user_id, {"status": status})


def authenticate_user(username: str, password: str) -> dict | None:
    """Authenticate a demo user and return the public record when successful."""
    user = get_user_by_username(username)
    if user is None or user["status"] != "active":
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return public_user(user)


def get_user_by_id_internal(user_id: int) -> dict | None:
    """Return a user record including password hash."""
    with connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return row_to_dict(row)


def delete_user(user_id: int) -> bool:
    """Delete an ops user."""
    with connection() as conn:
        cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0


def create_rpa_job(action: str, payload: dict, status: str, result: str) -> int:
    """Record an RPA simulation job."""
    with connection() as conn:
        cursor = conn.execute(
            "INSERT INTO rpa_jobs (action, payload, status, result) VALUES (?, ?, ?, ?)",
            (action, json.dumps(payload, ensure_ascii=False), status, result),
        )
        return int(cursor.lastrowid)


def get_rpa_jobs(limit: int = 20) -> list[dict]:
    """Return the most recent RPA job records."""
    with connection() as conn:
        cursor = conn.execute(
            "SELECT id, action, payload, status, result, created_at FROM rpa_jobs ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]
