import streamlit as st

from src.backup import download_backup_button


def render_backup_page():
    st.subheader("Backup")
    st.write("Exportald az adatokat JSON formatumban.")
    download_backup_button()
