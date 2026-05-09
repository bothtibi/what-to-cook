import json

import streamlit as st

from src.backup import download_backup_button, import_backup


def render_backup_page():
    st.subheader("Backup")
    st.write("Exportald az adatokat JSON formatumban.")
    download_backup_button()
    st.divider()
    st.write("Importalj backupot (V2).")
    import_mode = st.selectbox("Import mod", ["merge", "replace"])
    uploaded_file = st.file_uploader("JSON backup fajl", type=["json"])
    if uploaded_file and st.button("Import inditasa", type="primary"):
        try:
            payload = json.load(uploaded_file)
            import_backup(payload, mode=import_mode)
            st.success(f"Import kesz ({import_mode}).")
            st.rerun()
        except Exception as exc:
            st.error(f"Import hiba: {exc}")
