import json

import streamlit as st

from src.backup import download_backup_button, import_backup
from src.i18n import t


def render_backup_page():
    st.subheader(t("backup.title"))
    st.write(t("backup.export_help"))
    download_backup_button()
    st.divider()
    st.write(t("backup.import_help"))
    import_mode = st.selectbox(
        t("backup.mode"),
        ["merge", "replace"],
        format_func=lambda mode: t(f"backup.mode_{mode}"),
    )
    uploaded_file = st.file_uploader(t("backup.file"), type=["json"])
    if uploaded_file and st.button(t("backup.start"), type="primary"):
        try:
            payload = json.load(uploaded_file)
            import_backup(payload, mode=import_mode)
            st.success(t("backup.done", mode=import_mode))
            st.rerun()
        except Exception as exc:
            st.error(t("backup.error", error=exc))
