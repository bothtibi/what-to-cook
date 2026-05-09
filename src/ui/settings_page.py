import streamlit as st

from src.config import get_database_path
from src.db import get_active_backend_name


def render_settings_page():
    st.subheader("Beállítások")
    st.write("Ez az MVP verzió egyszerű, közös családi accounttal működik.")
    st.code(f"Aktív backend: {get_active_backend_name()}")
    st.code(f"Aktív adatbázis: {get_database_path()}")
