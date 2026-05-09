import streamlit as st

from src.auth import is_authenticated, login_form, logout
from src.db import init_db
from src.ui.backup_page import render_backup_page
from src.ui.history_page import render_history_page
from src.ui.recipes_page import render_recipes_page
from src.ui.recommendation_page import render_recommendation_page
from src.ui.settings_page import render_settings_page


st.set_page_config(page_title="Csaladi Fozes", layout="wide")
init_db()

if not is_authenticated():
    login_form()
    st.stop()

with st.sidebar:
    st.title("Menu")
    page = st.radio(
        "Oldalak",
        options=["Ajanlo", "Receptek", "History", "Backup", "Beallitasok"],
        label_visibility="collapsed",
    )
    if st.button("Kijelentkezes"):
        logout()
        st.rerun()

st.title("Csaladi fozes es receptkoveto")

if page == "Ajanlo":
    render_recommendation_page()
elif page == "Receptek":
    render_recipes_page()
elif page == "History":
    render_history_page()
elif page == "Backup":
    render_backup_page()
else:
    render_settings_page()