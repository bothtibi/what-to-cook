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
        background: #f6f7fb;
        color: #101828;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #121c2b 0%, #172435 100%);
        border-right: 1px solid #0f172a;
    }
    [data-testid="stSidebar"] * {
        color: #f8fafc;
    }
    [data-testid="stSidebar"] > div {
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] h1 {
        color: #ffffff;
        font-size: 1.15rem;
        line-height: 1.2;
        margin-bottom: 1rem;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #e5e7eb;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        border-radius: 10px;
        padding: 0.48rem 0.65rem;
        margin-bottom: 0.25rem;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid transparent;
        transition: background 120ms ease, border 120ms ease;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 255, 255, 0.12);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(180deg, #8b6df0 0%, #6d4bdc 100%);
        border-color: rgba(255, 255, 255, 0.24);
        box-shadow: 0 8px 18px rgba(91, 53, 213, 0.35);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label p {
        font-weight: 650;
        font-size: 0.92rem;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.18);
        color: #ffffff;
        width: 100%;
        margin-top: 1rem;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255, 255, 255, 0.16);
        border-color: rgba(255, 255, 255, 0.32);
        color: #ffffff;
    }
    .block-container {
        max-width: 1180px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }
    h1 {
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: 0;
        color: #101828;
    }
    h2, h3 {
        color: #101828;
        letter-spacing: 0;
    }
    [data-testid="stHeader"] {
        background: rgba(246, 247, 251, 0.9);
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #e7e9f0;
        border-radius: 14px;
        background: #ffffff;
        box-shadow: 0 10px 30px rgba(16, 24, 40, 0.05);
    }
    div[data-testid="stMetricValue"] {
        color: #101828;
        font-size: 1.5rem;
    }
    div[data-testid="stMetricLabel"] {
        color: #6b7280;
    }
    .stButton > button {
        border-radius: 8px;
        border: 1px solid #ddd6fe;
        background: #ffffff;
        color: #5b35d5;
        box-shadow: none;
        font-weight: 600;
    }
    .stButton > button:hover {
        border-color: #7c5ce8;
        color: #4f2fc3;
    }
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        border-radius: 8px;
        border: 1px solid #6d4bdc;
        background: linear-gradient(180deg, #7c5ce8 0%, #6042d0 100%);
        color: #ffffff;
        font-weight: 700;
    }
    .stDownloadButton > button:hover,
    .stFormSubmitButton > button:hover {
        border-color: #5638c8;
        background: #5638c8;
        color: #ffffff;
    }
    .stTextInput input,
    .stNumberInput input,
    textarea,
    [data-baseweb="select"] > div {
        border-radius: 8px;
        border-color: #e5e7eb;
    }
    div[role="radiogroup"] {
        gap: 0.35rem;
    }
    div[role="radiogroup"] label {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.35rem 0.65rem;
    }
    [data-baseweb="tag"] {
        border-radius: 6px;
    }
    .page-panel {
        background: #ffffff;
        border: 1px solid #e7e9f0;
        border-radius: 16px;
        padding: 1.25rem;
        box-shadow: 0 12px 34px rgba(16, 24, 40, 0.06);
        margin-bottom: 1rem;
    }
    .section-kicker {
        color: #667085;
        font-size: 0.85rem;
        margin-top: -0.35rem;
        margin-bottom: 1rem;
    }
    .recommend-card {
        border: 1px solid #e7e9f0;
        border-radius: 14px;
        background: #ffffff;
        padding: 0.9rem;
        min-height: 310px;
        box-shadow: 0 8px 26px rgba(16, 24, 40, 0.05);
        position: relative;
    }
    .rank-badge {
        position: absolute;
        top: -0.65rem;
        left: 0.75rem;
        width: 1.55rem;
        height: 1.55rem;
        border-radius: 999px;
        background: #7c5ce8;
        color: white;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .recipe-row {
        display: grid;
        grid-template-columns: 82px 1fr;
        gap: 0.8rem;
        align-items: center;
        margin: 0.45rem 0;
    }
    .recipe-thumb {
        width: 82px;
        height: 66px;
        border-radius: 14px;
        background: radial-gradient(circle at 32% 28%, #fff7d6 0%, #f2b84b 35%, #b45f1f 100%);
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.5), 0 8px 18px rgba(16,24,40,0.12);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #ffffff;
        font-weight: 800;
        font-size: 1.45rem;
        text-transform: uppercase;
    }
    .recipe-name {
        font-weight: 700;
        color: #101828;
        margin-bottom: 0.15rem;
    }
    .recipe-meta {
        color: #667085;
        font-size: 0.82rem;
    }
    .last-cooked {
        color: #667085;
        font-size: 0.78rem;
        margin-top: 0.22rem;
    }
    .difficulty-pill {
        display: inline-block;
        border-radius: 6px;
        padding: 0.08rem 0.38rem;
        font-size: 0.72rem;
        font-weight: 700;
        margin-left: 0.25rem;
        border: 1px solid #bbf7d0;
        color: #15803d;
        background: #f0fdf4;
    }
    .category-pill {
        display: inline-block;
        border-radius: 999px;
        padding: 0.12rem 0.48rem;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0;
        margin-right: 0.25rem;
        border: 1px solid transparent;
        white-space: nowrap;
    }
    .category-leves {
        background: #ecfdf3;
        color: #027a48;
        border-color: #abefc6;
    }
    .category-foetel {
        background: #fff4ed;
        color: #c4320a;
        border-color: #ffd6ae;
    }
    .category-reggeli {
        background: #eff8ff;
        color: #175cd3;
        border-color: #b2ddff;
    }
    .category-vacsora {
        background: #f4f3ff;
        color: #5925dc;
        border-color: #d9d6fe;
    }
    .category-other {
        background: #f2f4f7;
        color: #344054;
        border-color: #e4e7ec;
    }
    .combo-plus {
        color: #101828;
        text-align: center;
        font-weight: 800;
        font-size: 1.35rem;
        line-height: 1;
        margin: 0.15rem 0;
    }
    .card-note {
        color: #667085;
        font-size: 0.82rem;
        text-align: center;
        margin-top: 0.65rem;
        min-height: 1.2rem;
    }
    .list-row {
        border: 1px solid #e7e9f0;
        border-radius: 12px;
        padding: 0.75rem;
        background: #ffffff;
        margin-bottom: 0.55rem;
        box-shadow: 0 6px 18px rgba(16, 24, 40, 0.035);
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
        options=["Javaslatok", "Receptek", "Előzmények", "Rendszer"],
        label_visibility="collapsed",
    )
    if st.button("Kijelentkezés"):
        logout()
        st.rerun()

st.title("Családi főzés és receptkövető")

if page == "Javaslatok":
    render_recommendation_page()
elif page == "Receptek":
    render_recipes_page()
elif page == "Előzmények":
    render_history_page()
else:
    backup_tab, settings_tab = st.tabs(["Backup", "Beállítások"])
    with backup_tab:
        render_backup_page()
    with settings_tab:
        render_settings_page()
