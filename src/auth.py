import streamlit as st

from src.config import get_auth_config


def is_authenticated():
    return st.session_state.get("authenticated", False)


def login_form():
    st.title("Belepes")
    st.write("Csaladi kozos account")

    with st.form("login_form"):
        username = st.text_input("Felhasznalonev")
        password = st.text_input("Jelszo", type="password")
        submitted = st.form_submit_button("Belepes")

    if submitted:
        auth = get_auth_config()
        if username == auth["username"] and password == auth["password"]:
            st.session_state["authenticated"] = True
            st.success("Sikeres belepes")
            st.rerun()
        else:
            st.error("Hibas belepesi adatok")


def logout():
    st.session_state["authenticated"] = False
