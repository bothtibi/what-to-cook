from pathlib import Path

import streamlit as st


STYLE_DIR = Path(__file__).resolve().parent / "styles"
STYLE_FILES = [
    "base.css",
    "sidebar.css",
    "widgets.css",
    "recommendations.css",
    "recipes.css",
    "history.css",
]


def apply_global_styles():
    css = "\n".join((STYLE_DIR / file_name).read_text(encoding="utf-8") for file_name in STYLE_FILES)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
