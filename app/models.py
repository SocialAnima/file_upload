import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import bcrypt

from app.config import Config


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_db():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(default_password: str) -> None:
    Config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS files (
                id TEXT PRIMARY KEY,
                original_name TEXT NOT NULL,
                stored_name TEXT NOT NULL,
                size INTEGER NOT NULL,
                uploaded_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'password_hash'"
        ).fetchone()
        if row is None:
            password_hash = bcrypt.hashpw(
                default_password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            conn.execute(
                "INSERT INTO settings (key, value) VALUES ('password_hash', ?)",
                (password_hash,),
            )


def verify_password(password: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'password_hash'"
        ).fetchone()
    if row is None:
        return False
    return bcrypt.checkpw(password.encode("utf-8"), row["value"].encode("utf-8"))


def change_password(old_password: str, new_password: str) -> tuple[bool, str]:
    if not verify_password(old_password):
        return False, "原密码错误"
    if len(new_password) < 4:
        return False, "新密码至少 4 位"
    password_hash = bcrypt.hashpw(
        new_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    with get_db() as conn:
        conn.execute(
            "UPDATE settings SET value = ? WHERE key = 'password_hash'",
            (password_hash,),
        )
    return True, "密码修改成功"


def list_files() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, original_name, size, uploaded_at FROM files ORDER BY uploaded_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_file(file_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, original_name, stored_name, size, uploaded_at FROM files WHERE id = ?",
            (file_id,),
        ).fetchone()
    return dict(row) if row else None


def add_file(original_name: str, stored_name: str, size: int) -> dict:
    file_id = str(uuid.uuid4())
    uploaded_at = _now_iso()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO files (id, original_name, stored_name, size, uploaded_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (file_id, original_name, stored_name, size, uploaded_at),
        )
    return {
        "id": file_id,
        "original_name": original_name,
        "stored_name": stored_name,
        "size": size,
        "uploaded_at": uploaded_at,
    }


def delete_file(file_id: str) -> dict | None:
    file_record = get_file(file_id)
    if file_record is None:
        return None
    with get_db() as conn:
        conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
    stored_path = Config.UPLOAD_DIR / file_record["stored_name"]
    if stored_path.is_file():
        stored_path.unlink()
    return file_record


def get_stored_path(stored_name: str) -> Path:
    upload_root = Config.UPLOAD_DIR.resolve()
    path = (Config.UPLOAD_DIR / stored_name).resolve()
    if upload_root not in path.parents and path != upload_root:
        raise ValueError("Invalid file path")
    return path
