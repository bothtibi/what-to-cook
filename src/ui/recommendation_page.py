from datetime import date

import streamlit as st

from src.config import DEFAULT_CATEGORIES
from src.history import add_history_entry
from src.recommendations import recommend_recipes


def render_recommendation_page():
    st.subheader("Mit fozzunk?")
    col1, col2 = st.columns([2, 1])
    category = col1.selectbox("Kategoria (opcionalis)", [""] + DEFAULT_CATEGORIES)
    limit = col2.slider("Hany ajanlat legyen?", min_value=1, max_value=10, value=5)

    recipes = recommend_recipes(category=category, limit=limit)
    if not recipes:
        st.info("Nincs ajanlhato recept. Ellenorizd a receptlistat vagy a szuroket.")
        return

    stat1, stat2 = st.columns(2)
    stat1.metric("Javaslatok", len(recipes))
    stat2.metric("Aktiv kategoria", category or "mind")

    for recipe in recipes:
        with st.container(border=True):
            top_col1, top_col2 = st.columns([3, 2])
            top_col1.markdown(f"### {recipe['name']}")
            top_col2.caption(f"Kategoria: {recipe['category']} | Ido: {recipe['prep_time_minutes']} perc")
            if recipe["tags"]:
                st.caption(f"Tagek: {recipe['tags']}")
            st.write(recipe["ingredients_text"] or "-")

            with st.form(f"cook_{recipe['id']}"):
                st.caption("Ezt megfoztuk")
                cooked_date = st.date_input("Mikor?", value=date.today(), key=f"date_{recipe['id']}")
                days_planned = st.number_input("Hany napra fozve?", min_value=1, max_value=14, value=1, key=f"days_{recipe['id']}")
                quantity_note = st.text_input("Mennyiseg roviden", key=f"qty_{recipe['id']}")
                meal_group_id = st.text_input("Meal group ID (opcionalis)", key=f"group_{recipe['id']}")
                notes = st.text_area("Megjegyzes", key=f"note_{recipe['id']}")
                submit = st.form_submit_button("Mentes a history-ba")

            if submit:
                add_history_entry(
                    recipe_id=recipe["id"],
                    cooked_date=str(cooked_date),
                    days_planned=int(days_planned),
                    quantity_note=quantity_note.strip(),
                    meal_group_id=meal_group_id.strip(),
                    notes=notes.strip(),
                )
                st.success("History bejegyzes mentve.")
                st.rerun()
