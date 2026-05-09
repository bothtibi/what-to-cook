import sqlite3
from pathlib import Path

from src.config import get_database_path, get_turso_auth_token, get_turso_database_url

try:
    import libsql_client
except ImportError:  # pragma: no cover - optional at runtime
    libsql_client = None


def _sqlite_connection():
    db_path = Path(get_database_path())
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _use_turso():
    return bool(get_turso_database_url() and get_turso_auth_token() and libsql_client is not None)


def _row_to_dict(row, columns=None):
    if isinstance(row, dict):
        return row
    if hasattr(row, "asdict"):
        return row.asdict()
    try:
        return dict(row)
    except Exception:
        if columns and isinstance(row, (list, tuple)):
            return {col: row[idx] for idx, col in enumerate(columns)}
        return {"value": row}


def execute(sql, params=()):
    if _use_turso():
        url = get_turso_database_url()
        token = get_turso_auth_token()
        with libsql_client.create_client_sync(url=url, auth_token=token) as client:
            client.execute(sql, list(params))
        return

    conn = _sqlite_connection()
    with conn:
        conn.execute(sql, params)
    conn.close()


def fetchall(sql, params=()):
    if _use_turso():
        url = get_turso_database_url()
        token = get_turso_auth_token()
        with libsql_client.create_client_sync(url=url, auth_token=token) as client:
            result = client.execute(sql, list(params))
            columns = list(getattr(result, "columns", []))
            return [_row_to_dict(row, columns) for row in result.rows]

    conn = _sqlite_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetchone(sql, params=()):
    rows = fetchall(sql, params)
    return rows[0] if rows else None


def init_db():
    execute(
        """
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            prep_time_minutes INTEGER NOT NULL DEFAULT 0,
            difficulty TEXT NOT NULL DEFAULT '',
            ingredients_text TEXT NOT NULL DEFAULT '',
            instructions_text TEXT NOT NULL DEFAULT '',
            notes_text TEXT NOT NULL DEFAULT '',
            is_favorite INTEGER NOT NULL DEFAULT 0,
            is_blocked INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipe_id INTEGER NOT NULL,
            cooked_date TEXT NOT NULL,
            days_planned INTEGER NOT NULL DEFAULT 1,
            quantity_note TEXT NOT NULL DEFAULT '',
            meal_group_id TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            FOREIGN KEY(recipe_id) REFERENCES recipes(id)
        )
        """
    )
