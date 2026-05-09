from src.db import execute, fetchall


def add_history_entry(recipe_id, cooked_date, days_planned, quantity_note, meal_group_id, notes):
    execute(
        """
        INSERT INTO history
        (recipe_id, cooked_date, days_planned, quantity_note, meal_group_id, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (recipe_id, cooked_date, days_planned, quantity_note, meal_group_id, notes),
    )


def list_history(start_date=None, end_date=None, query=""):
    sql = """
        SELECT h.*, r.name AS recipe_name, r.category
        FROM history h
        JOIN recipes r ON r.id = h.recipe_id
        WHERE 1=1
    """
    params = []

    if start_date:
        sql += " AND h.cooked_date >= ?"
        params.append(str(start_date))
    if end_date:
        sql += " AND h.cooked_date <= ?"
        params.append(str(end_date))
    if query:
        sql += " AND LOWER(r.name) LIKE ?"
        params.append(f"%{query.lower()}%")

    sql += " ORDER BY h.cooked_date DESC, h.id DESC"
    return fetchall(sql, tuple(params))


def recent_cooked_dates_by_recipe():
    rows = fetchall(
        """
        SELECT recipe_id, MAX(cooked_date) AS last_cooked_date, COUNT(*) AS cooked_count
        FROM history
        GROUP BY recipe_id
        """,
        (),
    )
    return {row["recipe_id"]: row for row in rows}
