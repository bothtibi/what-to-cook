import streamlit as st

from src.auth import is_authenticated, login_form, logout
from src.db import init_db
from src.ui.backup_page import render_backup_page
from src.ui.history_page import render_history_page
from src.ui.recipes_page import render_recipes_page
from src.ui.recommendation_page import render_recommendation_page
from src.ui.settings_page import render_settings_page


st.set_page_config(page_title="Családi főzés", layout="wide")
init_db()

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(180deg, #f8f9ff 0%, #f4f6ff 100%);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1f2937 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e5e7eb;
    }
    .block-container {
        padding-top: 1.2rem;
    }
    div[data-testid="stMetricValue"] {
        color: #4f46e5;
    }
    .stButton > button {
        border-radius: 10px;
        border: 1px solid #6366f1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if not is_authenticated():
    login_form()
    st.stop()

with st.sidebar:
    st.title("Mit főzzünk?")
    page = st.radio(
        "Oldalak",
        options=["Javaslatok", "Receptek", "Előzmények", "Backup", "Beállítások"],
        label_visibility="collapsed",
    )
    if st.button("Kijelentkezes"):
        logout()
        st.rerun()

st.title("Családi főzés és receptkövető")

if page == "Javaslatok":
    render_recommendation_page()
elif page == "Receptek":
    render_recipes_page()
elif page == "Előzmények":
    render_history_page()
elif page == "Backup":
    render_backup_page()
else:
    render_settings_page()