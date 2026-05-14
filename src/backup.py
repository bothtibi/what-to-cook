import json
from datetime import date, datetime

import streamlit as st

from src.db import execute, execute_many, execute_transaction, fetchall, fetchone
from src.i18n import t


def build_backup_payload():
    recipes = fetchall("SELECT * FROM recipes ORDER BY id")
    history = fetchall("SELECT * FROM history ORDER BY id")

    tags = sorted(
        {
            tag.strip().lower()
            for recipe in recipes
            for tag in recipe["tags"].split(",")
            if tag.strip()
        }
    )

    combinations = []
    grouped = {}
    for item in history:
        if item["meal_group_id"]:
            grouped.setdefault(item["meal_group_id"], []).append(item["recipe_id"])
    for meal_group_id, recipe_ids in grouped.items():
        combinations.append({"meal_group_id": meal_group_id, "recipe_ids": sorted(set(recipe_ids))})

    return {
        "schema_version": 2,
        "exported_at": datetime.utcnow().isoformat(),
        "recipes": recipes,
        "history": history,
        "tags": tags,
        "combinations": combinations,
    }


def download_backup_button():
    payload = build_backup_payload()
    st.download_button(
        label=t("backup.download"),
        data=json.dumps(payload, ensure_ascii=False, indent=2),
        file_name="meal_memory_backup.json",
        mime="application/json",
    )


def _cooked_date_or_default(value):
    if not value:
        return date.today().isoformat()
    date.fromisoformat(str(value))
    return str(value)


def _recipe_replace_row(item):
    return (
        item.get("id"),
        item.get("name", ""),
        item.get("category", ""),
        item.get("tags", ""),
        int(item.get("prep_time_minutes", 0)),
        item.get("difficulty", ""),
        item.get("ingredients_text", ""),
        item.get("instructions_text", ""),
        item.get("notes_text", ""),
        int(item.get("is_favorite", 0)),
        int(item.get("is_blocked", 0)),
        int(item.get("favorite_tibi", 0)),
        int(item.get("favorite_melinda", 0)),
        int(item.get("dislike_tibi", 0)),
        int(item.get("dislike_melinda", 0)),
        item.get("created_at") or datetime.utcnow().isoformat(),
        item.get("updated_at") or datetime.utcnow().isoformat(),
    )


def _history_replace_row(item, valid_recipe_ids):
    recipe_id = item.get("recipe_id")
    if recipe_id not in valid_recipe_ids:
        raise ValueError(f"History references missing recipe_id: {recipe_id}")
    return (
        item.get("id"),
        recipe_id,
        _cooked_date_or_default(item.get("cooked_date")),
        int(item.get("days_planned", 1)),
        item.get("quantity_note", ""),
        item.get("meal_group_id", ""),
        item.get("notes", ""),
    )


def import_backup(payload, mode="merge"):
    recipes = payload.get("recipes", [])
    history = payload.get("history", [])

    if mode == "replace":
        recipe_rows = [_recipe_replace_row(item) for item in recipes]
        valid_recipe_ids = {row[0] for row in recipe_rows}
        history_rows = [_history_replace_row(item, valid_recipe_ids) for item in history]

        statements = [
            ("DELETE FROM history", ()),
            ("DELETE FROM recipes", ()),
        ]
        statements.extend(
            (
                """
                INSERT INTO recipes
                (id, name, category, tags, prep_time_minutes, difficulty, ingredients_text,
                 instructions_text, notes_text, is_favorite, is_blocked,
                 favorite_tibi, favorite_melinda, dislike_tibi, dislike_melinda,
                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                row,
            )
            for row in recipe_rows
        )
        statements.extend(
            (
                """
                INSERT INTO history
                (id, recipe_id, cooked_date, days_planned, quantity_note, meal_group_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                row,
            )
            for row in history_rows
        )
        execute_transaction(statements)
        return

    old_to_new_ids = {}
    for item in recipes:
        recipe_name = (item.get("name", "") or "").strip()
        if not recipe_name:
            continue

        existing = fetchone("SELECT id FROM recipes WHERE LOWER(name) = ?", (recipe_name.lower(),))
        if existing:
            old_to_new_ids[item.get("id")] = existing["id"]
            continue

        execute(
            """
            INSERT INTO recipes
            (name, category, tags, prep_time_minutes, difficulty, ingredients_text,
             instructions_text, notes_text, is_favorite, is_blocked,
             favorite_tibi, favorite_melinda, dislike_tibi, dislike_melinda,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recipe_name,
                item.get("category", ""),
                item.get("tags", ""),
                int(item.get("prep_time_minutes", 0)),
                item.get("difficulty", ""),
                item.get("ingredients_text", ""),
                item.get("instructions_text", ""),
                item.get("notes_text", ""),
                int(item.get("is_favorite", 0)),
                int(item.get("is_blocked", 0)),
                int(item.get("favorite_tibi", 0)),
                int(item.get("favorite_melinda", 0)),
                int(item.get("dislike_tibi", 0)),
                int(item.get("dislike_melinda", 0)),
                item.get("created_at") or datetime.utcnow().isoformat(),
                item.get("updated_at") or datetime.utcnow().isoformat(),
            ),
        )
        inserted = fetchone("SELECT id FROM recipes WHERE LOWER(name) = ?", (recipe_name.lower(),))
        if inserted:
            old_to_new_ids[item.get("id")] = inserted["id"]

    history_rows = []
    for item in history:
        mapped_recipe_id = old_to_new_ids.get(item.get("recipe_id"))
        if not mapped_recipe_id:
            continue
        history_rows.append(
            (
                mapped_recipe_id,
                _cooked_date_or_default(item.get("cooked_date")),
                int(item.get("days_planned", 1)),
                item.get("quantity_note", ""),
                item.get("meal_group_id", ""),
                item.get("notes", ""),
            )
        )

    execute_many(
        """
        INSERT INTO history
        (recipe_id, cooked_date, days_planned, quantity_note, meal_group_id, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        history_rows,
    )
