from datetime import date

import streamlit as st

from src.config import DEFAULT_CATEGORIES
from src.history import add_history_entry
from src.recommendations import recommend_recipes


def render_recommendation_page():
    st.subheader("Mit fozzunk?")
    category = st.selectbox("Kategoria (opcionalis)", [""] + DEFAULT_CATEGORIES)
    limit = st.slider("Hany ajanlat legyen?", min_value=1, max_value=10, value=5)

    recipes = recommend_recipes(category=category, limit=limit)
    if not recipes:
        st.info("Nincs ajanlhato recept. Ellenorizd a receptlistat vagy a szuroket.")
        return

    for recipe in recipes:
        with st.container(border=True):
            st.markdown(f"### {recipe['name']}")
            st.write(f"Kategoria: {recipe['category']} | Ido: {recipe['prep_time_minutes']} perc")
            if recipe["tags"]:
                st.write(f"Tagek: {recipe['tags']}")
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
