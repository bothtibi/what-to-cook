import json
from datetime import datetime

import streamlit as st

from src.db import fetchall


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

    return {
        "exported_at": datetime.utcnow().isoformat(),
        "recipes": recipes,
        "history": history,
        "tags": tags,
        "combinations": [],
    }


def download_backup_button():
    payload = build_backup_payload()
    st.download_button(
        label="JSON export letoltese",
        data=json.dumps(payload, ensure_ascii=False, indent=2),
        file_name="meal_memory_backup.json",
        mime="application/json",
    )
