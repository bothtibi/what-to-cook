from src.db import execute, fetchall, fetchone


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


def create_recipe(data):
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
            normalize_category(data["category"]),
            normalize_tags(data["tags"]),
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
            normalize_category(data["category"]),
            normalize_tags(data["tags"]),
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


def get_recipe(recipe_id):
    return fetchone("SELECT * FROM recipes WHERE id = ?", (recipe_id,))


def list_recipes(query="", category="", tag="", include_disliked=True):
    sql = "SELECT * FROM recipes WHERE 1=1"
    params = []

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

    sql += " ORDER BY updated_at DESC, name ASC"
    return fetchall(sql, tuple(params))
