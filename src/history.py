from src.db import execute, execute_transaction, fetchall


def _clean_history_value(value):
    return "" if value is None else str(value).strip()


def _clean_days(value):
    try:
        return max(int(value), 1)
    except (TypeError, ValueError):
        return 1


def clean_history_entry(entry):
    return {
        "recipe_id": int(entry["recipe_id"]),
        "cooked_date": _clean_history_value(entry["cooked_date"]),
        "days_planned": _clean_days(entry.get("days_planned", 1)),
        "quantity_note": _clean_history_value(entry.get("quantity_note", "")),
        "meal_group_id": _clean_history_value(entry.get("meal_group_id", "")),
        "notes": _clean_history_value(entry.get("notes", "")),
    }


def add_history_entry(recipe_id, cooked_date, days_planned, quantity_note, meal_group_id, notes):
    entry = clean_history_entry(
        {
            "recipe_id": recipe_id,
            "cooked_date": cooked_date,
            "days_planned": days_planned,
            "quantity_note": quantity_note,
            "meal_group_id": meal_group_id,
            "notes": notes,
        }
    )
    execute(
        """
        INSERT INTO history
        (recipe_id, cooked_date, days_planned, quantity_note, meal_group_id, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            entry["recipe_id"],
            entry["cooked_date"],
            entry["days_planned"],
            entry["quantity_note"],
            entry["meal_group_id"],
            entry["notes"],
        ),
    )


def add_history_entries(entries):
    cleaned_entries = [clean_history_entry(entry) for entry in entries]
    execute_transaction(
        [
            (
                """
                INSERT INTO history
                (recipe_id, cooked_date, days_planned, quantity_note, meal_group_id, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entry["recipe_id"],
                    entry["cooked_date"],
                    entry["days_planned"],
                    entry["quantity_note"],
                    entry["meal_group_id"],
                    entry["notes"],
                ),
            )
            for entry in cleaned_entries
        ]
    )


def update_history_entry(history_id, cooked_date, days_planned, quantity_note, notes):
    execute(
        """
        UPDATE history
        SET cooked_date = ?, days_planned = ?, quantity_note = ?, notes = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            _clean_history_value(cooked_date),
            _clean_days(days_planned),
            _clean_history_value(quantity_note),
            _clean_history_value(notes),
            history_id,
        ),
    )


def delete_history_entry(history_id):
    execute("DELETE FROM history WHERE id = ?", (history_id,))


def delete_history_group(meal_group_id):
    execute("DELETE FROM history WHERE meal_group_id = ?", (_clean_history_value(meal_group_id),))


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
