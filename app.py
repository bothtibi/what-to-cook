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
        background: #f7f7f5;
        color: #1f2933;
    }
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e7eb;
    }
    [data-testid="stSidebar"] * {
        color: #1f2933;
    }
    .block-container {
        max-width: 1120px;
        padding-top: 1.4rem;
        padding-bottom: 3rem;
    }
    h1 {
        font-size: 2rem;
        font-weight: 650;
        letter-spacing: 0;
        color: #111827;
    }
    h2, h3 {
        color: #111827;
        letter-spacing: 0;
    }
    [data-testid="stHeader"] {
        background: rgba(247, 247, 245, 0.92);
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #e5e7eb;
        border-radius: 8px;
        background: #ffffff;
    }
    div[data-testid="stMetricValue"] {
        color: #1f2933;
        font-size: 1.5rem;
    }
    div[data-testid="stMetricLabel"] {
        color: #6b7280;
    }
    .stButton > button {
        border-radius: 8px;
        border: 1px solid #d1d5db;
        background: #ffffff;
        color: #1f2933;
        box-shadow: none;
    }
    .stButton > button:hover {
        border-color: #9ca3af;
        color: #111827;
    }
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        border-radius: 8px;
        border: 1px solid #111827;
        background: #111827;
        color: #ffffff;
    }
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {
        border-color: #374151;
        background: #374151;
        color: #ffffff;
    }
    [data-baseweb="tag"] {
        border-radius: 6px;
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
