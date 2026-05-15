import streamlit as st

from src.config import get_auth_config
from src.i18n import t


def is_authenticated():
    return st.session_state.get("authenticated", False)


def login_form():
    st.title(t("auth.title"))
    st.write(t("auth.subtitle"))

    with st.form("login_form", enter_to_submit=False):
        username = st.text_input(t("auth.username"))
        password = st.text_input(t("auth.password"), type="password")
        submitted = st.form_submit_button(t("auth.submit"))

    if submitted:
        auth = get_auth_config()
        if username == auth["username"] and password == auth["password"]:
            st.session_state["authenticated"] = True
            st.success(t("auth.success"))
            st.rerun()
        else:
            st.error(t("auth.error"))


def logout():
    st.session_state["authenticated"] = False
