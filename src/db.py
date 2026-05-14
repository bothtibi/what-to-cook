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


def execute_many(sql, param_sets):
    execute_transaction([(sql, params) for params in param_sets])


def execute_transaction(statements):
    if not statements:
        return

    if _use_turso():
        url = get_turso_database_url()
        token = get_turso_auth_token()
        with libsql_client.create_client_sync(url=url, auth_token=token) as client:
            client.execute("BEGIN")
            try:
                for sql, params in statements:
                    client.execute(sql, list(params))
                client.execute("COMMIT")
            except Exception:
                client.execute("ROLLBACK")
                raise
        return

    conn = _sqlite_connection()
    try:
        with conn:
            for sql, params in statements:
                conn.execute(sql, params)
    finally:
        conn.close()


def get_active_backend_name():
    return "turso" if _use_turso() else "sqlite"


def init_db():
    execute(
        """
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '',
            prep_time_minutes INTEGER NOT NULL DEFAULT 0,
            difficulty TEXT NOT NULL DEFAULT 'Közepes',
            ingredients_text TEXT NOT NULL DEFAULT '',
            instructions_text TEXT NOT NULL DEFAULT '',
            notes_text TEXT NOT NULL DEFAULT '',
            is_favorite INTEGER NOT NULL DEFAULT 0,
            is_blocked INTEGER NOT NULL DEFAULT 0,
            is_archived INTEGER NOT NULL DEFAULT 0,
            favorite_tibi INTEGER NOT NULL DEFAULT 0,
            favorite_melinda INTEGER NOT NULL DEFAULT 0,
            dislike_tibi INTEGER NOT NULL DEFAULT 0,
            dislike_melinda INTEGER NOT NULL DEFAULT 0,
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
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(recipe_id) REFERENCES recipes(id)
        )
        """
    )
    recipe_columns = {col["name"] for col in fetchall("PRAGMA table_info(recipes)")}
    if "favorite_tibi" not in recipe_columns:
        execute("ALTER TABLE recipes ADD COLUMN favorite_tibi INTEGER NOT NULL DEFAULT 0")
    if "favorite_melinda" not in recipe_columns:
        execute("ALTER TABLE recipes ADD COLUMN favorite_melinda INTEGER NOT NULL DEFAULT 0")
    if "dislike_tibi" not in recipe_columns:
        execute("ALTER TABLE recipes ADD COLUMN dislike_tibi INTEGER NOT NULL DEFAULT 0")
    if "dislike_melinda" not in recipe_columns:
        execute("ALTER TABLE recipes ADD COLUMN dislike_melinda INTEGER NOT NULL DEFAULT 0")
    if "is_archived" not in recipe_columns:
        execute("ALTER TABLE recipes ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0")
    history_columns = {col["name"] for col in fetchall("PRAGMA table_info(history)")}
    if "created_at" not in history_columns:
        execute("ALTER TABLE history ADD COLUMN created_at TEXT NOT NULL DEFAULT ''")
        execute("UPDATE history SET created_at = CURRENT_TIMESTAMP WHERE created_at = ''")
    if "updated_at" not in history_columns:
        execute("ALTER TABLE history ADD COLUMN updated_at TEXT NOT NULL DEFAULT ''")
        execute("UPDATE history SET updated_at = CURRENT_TIMESTAMP WHERE updated_at = ''")
    execute(
        """
        UPDATE recipes
        SET favorite_tibi = 1
        WHERE is_favorite = 1 AND favorite_tibi = 0 AND favorite_melinda = 0
        """
    )
    execute(
        """
        UPDATE recipes
        SET dislike_tibi = 1, dislike_melinda = 1
        WHERE is_blocked = 1 AND dislike_tibi = 0 AND dislike_melinda = 0
        """
    )
    execute("UPDATE recipes SET category = 'Leves' WHERE LOWER(category) IN ('leves')")
    execute("UPDATE recipes SET category = 'Főétel' WHERE LOWER(category) IN ('foetel', 'főétel')")
    execute("UPDATE recipes SET category = 'Reggeli' WHERE LOWER(category) IN ('reggeli')")
    execute("UPDATE recipes SET category = 'Vacsora' WHERE LOWER(category) IN ('vacsora')")
