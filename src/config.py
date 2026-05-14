import os

import streamlit as st


DEFAULT_CATEGORIES = ["Leves", "Főétel", "Reggeli", "Vacsora"]
RECIPE_DIFFICULTIES = ["Könnyű", "Közepes", "Nehéz"]


def get_secret(name, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.getenv(name, default)


def get_auth_config():
    return {
        "username": get_secret("APP_USERNAME", "family"),
        "password": get_secret("APP_PASSWORD", "family123"),
    }


def get_database_path():
    return get_secret("DB_PATH", "data/app.db")


def get_turso_database_url():
    return get_secret("TURSO_DATABASE_URL", "")


def get_turso_auth_token():
    return get_secret("TURSO_AUTH_TOKEN", "")
