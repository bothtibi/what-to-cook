import streamlit as st

from src.auth import is_authenticated, login_form, logout
from src.db import init_db
from src.i18n import t
from src.ui.backup_page import render_backup_page
from src.ui.history_page import render_history_page
from src.ui.recipes_page import render_recipes_page
from src.ui.recommendation_page import render_recommendation_page
from src.ui.settings_page import render_settings_page
from src.ui.styles import apply_global_styles


st.set_page_config(page_title=t("app.page_title"), layout="wide", initial_sidebar_state="expanded")
init_db()
apply_global_styles()

if not is_authenticated():
    login_form()
    st.stop()

with st.sidebar:
    st.title(t("app.sidebar_title"))
    valid_pages = {"recommendations", "recipes", "history", "system"}
    if st.session_state.get("active_page") not in valid_pages:
        st.session_state["active_page"] = "recommendations"

    nav_items = [
        ("recommendations", t("nav.recommendations")),
        ("recipes", t("nav.recipes")),
        ("history", t("nav.history")),
        ("system", t("nav.system")),
    ]
    for page_key, label in nav_items:
        active = st.session_state["active_page"] == page_key
        if st.button(label, key=f"nav_{page_key}", type="primary" if active else "secondary"):
            st.session_state["active_page"] = page_key
            st.session_state.pop("recipe_preview_id", None)
            st.session_state.pop("cook_modal", None)
            st.rerun()

page = st.session_state["active_page"]
st.title(t("app.title"))

if page == "recommendations":
    render_recommendation_page()
elif page == "recipes":
    render_recipes_page()
elif page == "history":
    render_history_page()
else:
    settings_tab, backup_tab = st.tabs([t("tabs.settings"), t("tabs.backup")])
    with settings_tab:
        render_settings_page()
        st.divider()
        if st.button(t("nav.logout"), type="primary"):
            logout()
            st.rerun()
    with backup_tab:
        render_backup_page()
