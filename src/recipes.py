from src.db import execute, fetchall, fetchone


def normalize_tags(tags_text):
    tags = [tag.strip().lower() for tag in tags_text.split(",") if tag.strip()]
    unique_tags = list(dict.fromkeys(tags))
    return ", ".join(unique_tags)


def create_recipe(data):
    execute(
        """
        INSERT INTO recipes
        (name, category, tags, prep_time_minutes, difficulty, ingredients_text,
         instructions_text, notes_text, is_favorite, is_blocked)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["name"],
            data["category"],
            normalize_tags(data["tags"]),
            data["prep_time_minutes"],
            data["difficulty"],
            data["ingredients_text"],
            data["instructions_text"],
            data["notes_text"],
            int(data["is_favorite"]),
            int(data["is_blocked"]),
        ),
    )


def update_recipe(recipe_id, data):
    execute(
        """
        UPDATE recipes
        SET name = ?, category = ?, tags = ?, prep_time_minutes = ?, difficulty = ?,
            ingredients_text = ?, instructions_text = ?, notes_text = ?,
            is_favorite = ?, is_blocked = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            data["name"],
            data["category"],
            normalize_tags(data["tags"]),
            data["prep_time_minutes"],
            data["difficulty"],
            data["ingredients_text"],
            data["instructions_text"],
            data["notes_text"],
            int(data["is_favorite"]),
            int(data["is_blocked"]),
            recipe_id,
        ),
    )


def get_recipe(recipe_id):
    return fetchone("SELECT * FROM recipes WHERE id = ?", (recipe_id,))


def list_recipes(query="", category="", tag="", include_blocked=True):
    sql = "SELECT * FROM recipes WHERE 1=1"
    params = []

    if query:
        sql += " AND LOWER(name) LIKE ?"
        params.append(f"%{query.lower()}%")
    if category:
        sql += " AND category = ?"
        params.append(category)
    if tag:
        sql += " AND LOWER(tags) LIKE ?"
        params.append(f"%{tag.lower()}%")
    if not include_blocked:
        sql += " AND is_blocked = 0"

    sql += " ORDER BY updated_at DESC, name ASC"
    return fetchall(sql, tuple(params))
