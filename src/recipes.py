import streamlit as st

from src.db import execute, execute_transaction, fetchall, fetchone


VALID_CATEGORIES = {"Leves", "Főétel", "Reggeli", "Vacsora"}
VALID_DIFFICULTIES = {"Könnyű", "Közepes", "Nehéz"}


def normalize_category(category):
    raw = (category or "").strip()
    key = raw.lower()
    mapping = {
        "leves": "Leves",
        "főétel": "Főétel",
        "foetel": "Főétel",
        "reggeli": "Reggeli",
        "vacsora": "Vacsora",
    }
    return mapping.get(key, raw)


def _category_variants_for_filter(category):
    normalized = normalize_category(category)
    if normalized == "Főétel":
        return ["Főétel", "foetel", "Foetel", "főétel"]
    if normalized:
        return [normalized, normalized.lower()]
    return []


def normalize_tags(tags_text):
    tags = [tag.strip().lower() for tag in tags_text.split(",") if tag.strip()]
    unique_tags = list(dict.fromkeys(tags))
    return ", ".join(unique_tags)


def normalize_difficulty(difficulty):
    raw = (difficulty or "").strip()
    key = raw.lower()
    mapping = {
        "könnyű": "Könnyű",
        "konnyu": "Könnyű",
        "easy": "Könnyű",
        "közepes": "Közepes",
        "kozepes": "Közepes",
        "medium": "Közepes",
        "nehéz": "Nehéz",
        "nehez": "Nehéz",
        "hard": "Nehéz",
    }
    return mapping.get(key, raw or "Közepes")


def clean_recipe_data(data):
    category = normalize_category(data.get("category", ""))
    difficulty = normalize_difficulty(data.get("difficulty", ""))
    return {
        "name": data.get("name", "").strip(),
        "category": category if category in VALID_CATEGORIES else "Főétel",
        "tags": normalize_tags(data.get("tags", "")),
        "prep_time_minutes": max(int(data.get("prep_time_minutes", 0) or 0), 0),
        "difficulty": difficulty if difficulty in VALID_DIFFICULTIES else "Közepes",
        "ingredients_text": data.get("ingredients_text", "").strip(),
        "instructions_text": data.get("instructions_text", "").strip(),
        "notes_text": data.get("notes_text", "").strip(),
        "favorite_tibi": bool(data.get("favorite_tibi", False)),
        "favorite_melinda": bool(data.get("favorite_melinda", False)),
        "dislike_tibi": bool(data.get("dislike_tibi", False)),
        "dislike_melinda": bool(data.get("dislike_melinda", False)),
    }


def validate_recipe_data(data):
    cleaned = clean_recipe_data(data)
    errors = []
    if not cleaned["name"]:
        errors.append("name")
    if not cleaned["ingredients_text"]:
        errors.append("ingredients")
    if not cleaned["instructions_text"]:
        errors.append("instructions")
    return cleaned, errors


def create_recipe(data):
    data = clean_recipe_data(data)
    favorite_any = bool(data["favorite_tibi"] or data["favorite_melinda"])
    disliked_by_both = bool(data["dislike_tibi"] and data["dislike_melinda"])
    execute(
        """
        INSERT INTO recipes
        (name, category, tags, prep_time_minutes, difficulty, ingredients_text,
         instructions_text, notes_text, is_favorite, is_blocked,
         favorite_tibi, favorite_melinda, dislike_tibi, dislike_melinda)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["name"],
            data["category"],
            data["tags"],
            data["prep_time_minutes"],
            data["difficulty"],
            data["ingredients_text"],
            data["instructions_text"],
            data["notes_text"],
            int(favorite_any),
            int(disliked_by_both),
            int(data["favorite_tibi"]),
            int(data["favorite_melinda"]),
            int(data["dislike_tibi"]),
            int(data["dislike_melinda"]),
        ),
    )


def update_recipe(recipe_id, data):
    data = clean_recipe_data(data)
    favorite_any = bool(data["favorite_tibi"] or data["favorite_melinda"])
    disliked_by_both = bool(data["dislike_tibi"] and data["dislike_melinda"])
    execute(
        """
        UPDATE recipes
        SET name = ?, category = ?, tags = ?, prep_time_minutes = ?, difficulty = ?,
            ingredients_text = ?, instructions_text = ?, notes_text = ?,
            is_favorite = ?, is_blocked = ?,
            favorite_tibi = ?, favorite_melinda = ?, dislike_tibi = ?, dislike_melinda = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            data["name"],
            data["category"],
            data["tags"],
            data["prep_time_minutes"],
            data["difficulty"],
            data["ingredients_text"],
            data["instructions_text"],
            data["notes_text"],
            int(favorite_any),
            int(disliked_by_both),
            int(data["favorite_tibi"]),
            int(data["favorite_melinda"]),
            int(data["dislike_tibi"]),
            int(data["dislike_melinda"]),
            recipe_id,
        ),
    )


def recipe_name_exists(name, exclude_id=None):
    sql = "SELECT id FROM recipes WHERE LOWER(name) = ?"
    params = [name.strip().lower()]
    if exclude_id is not None:
        sql += " AND id != ?"
        params.append(exclude_id)
    return fetchone(sql, tuple(params)) is not None


def set_favorite_tibi(recipe_id, enabled):
    execute(
        """
        UPDATE recipes
        SET favorite_tibi = ?,
            is_favorite = CASE WHEN (? = 1 OR favorite_melinda = 1) THEN 1 ELSE 0 END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (int(enabled), int(enabled), recipe_id),
    )


def set_favorite_melinda(recipe_id, enabled):
    execute(
        """
        UPDATE recipes
        SET favorite_melinda = ?,
            is_favorite = CASE WHEN (favorite_tibi = 1 OR ? = 1) THEN 1 ELSE 0 END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (int(enabled), int(enabled), recipe_id),
    )


def set_dislike_tibi(recipe_id, enabled):
    execute(
        """
        UPDATE recipes
        SET dislike_tibi = ?,
            is_blocked = CASE WHEN (? = 1 AND dislike_melinda = 1) THEN 1 ELSE 0 END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (int(enabled), int(enabled), recipe_id),
    )


def set_dislike_melinda(recipe_id, enabled):
    execute(
        """
        UPDATE recipes
        SET dislike_melinda = ?,
            is_blocked = CASE WHEN (dislike_tibi = 1 AND ? = 1) THEN 1 ELSE 0 END,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (int(enabled), int(enabled), recipe_id),
    )


@st.cache_data(ttl=60)
def get_recipe(recipe_id):
    return fetchone("SELECT * FROM recipes WHERE id = ? AND is_archived = 0", (recipe_id,))


def archive_recipe(recipe_id):
    execute("UPDATE recipes SET is_archived = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (recipe_id,))


def restore_recipe(recipe_id):
    execute("UPDATE recipes SET is_archived = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (recipe_id,))


def delete_recipe(recipe_id):
    execute_transaction(
        [
            ("DELETE FROM history WHERE recipe_id = ?", (recipe_id,)),
            ("DELETE FROM recipes WHERE id = ?", (recipe_id,)),
        ]
    )


@st.cache_data(ttl=60)
def list_recipes(query="", category="", tag="", include_disliked=True, include_archived=False):
    sql = "SELECT * FROM recipes WHERE 1=1"
    params = []

    if not include_archived:
        sql += " AND is_archived = 0"
    if query:
        sql += " AND LOWER(name) LIKE ?"
        params.append(f"%{query.lower()}%")
    if category:
        variants = _category_variants_for_filter(category)
        placeholders = ", ".join(["?"] * len(variants))
        sql += f" AND category IN ({placeholders})"
        params.extend(variants)
    if tag:
        sql += " AND LOWER(tags) LIKE ?"
        params.append(f"%{tag.lower()}%")
    if not include_disliked:
        sql += " AND NOT (dislike_tibi = 1 AND dislike_melinda = 1)"

    sql += " ORDER BY is_archived ASC, updated_at DESC, name ASC"
    return fetchall(sql, tuple(params))
