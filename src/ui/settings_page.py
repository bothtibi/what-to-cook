import streamlit as st

from src.config import get_database_path
from src.db import get_active_backend_name


def render_settings_page():
    st.subheader("Beallitasok")
    st.write("Ez az MVP verzio egyszeru, kozos csaladi accounttal mukodik.")
    st.code(f"Aktiv backend: {get_active_backend_name()}")
    st.code(f"Aktiv adatbazis: {get_database_path()}")
