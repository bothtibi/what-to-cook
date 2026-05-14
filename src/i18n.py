import json
from functools import lru_cache
from pathlib import Path

import streamlit as st


DEFAULT_LANGUAGE = "hu"
SUPPORTED_LANGUAGES = {
    "hu": "Magyar",
    "en": "English",
}


@lru_cache(maxsize=None)
def _load_translations(language):
    path = Path(__file__).parent / "locales" / f"{language}.json"
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def get_language():
    return st.session_state.get("language", DEFAULT_LANGUAGE)


def set_language(language):
    if language in SUPPORTED_LANGUAGES:
        st.session_state["language"] = language


def t(key, **kwargs):
    translations = _load_translations(get_language())
    text = translations.get(key)
    if text is None and get_language() != DEFAULT_LANGUAGE:
        text = _load_translations(DEFAULT_LANGUAGE).get(key)
    if text is None:
        text = key
    return text.format(**kwargs) if kwargs else text


def category_label(category):
    normalized = str(category).strip().lower()
    mapping = {
        "leves": "category.leves",
        "főétel": "category.foetel",
        "foetel": "category.foetel",
        "reggeli": "category.reggeli",
        "vacsora": "category.vacsora",
    }
    key = mapping.get(normalized)
    return t(key) if key else str(category)


def difficulty_label(difficulty):
    normalized = str(difficulty).strip().lower()
    mapping = {
        "könnyű": "difficulty.easy",
        "konnyu": "difficulty.easy",
        "közepes": "difficulty.medium",
        "kozepes": "difficulty.medium",
        "nehéz": "difficulty.hard",
        "nehez": "difficulty.hard",
    }
    key = mapping.get(normalized)
    return t(key) if key else str(difficulty)
