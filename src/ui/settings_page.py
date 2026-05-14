import streamlit as st

from src.config import get_database_path
from src.db import get_active_backend_name
from src.i18n import SUPPORTED_LANGUAGES, get_language, set_language, t


def render_settings_page():
    st.subheader(t("settings.title"))
    st.write(t("settings.description"))

    language_codes = list(SUPPORTED_LANGUAGES.keys())
    current_language = get_language()
    selected_language = st.selectbox(
        t("settings.language"),
        language_codes,
        index=language_codes.index(current_language) if current_language in language_codes else 0,
        format_func=lambda code: SUPPORTED_LANGUAGES[code],
        help=t("settings.language_help"),
    )
    if selected_language != current_language:
        set_language(selected_language)
        st.rerun()

    st.code(t("settings.backend", backend=get_active_backend_name()))
    st.code(t("settings.database", database=get_database_path()))
