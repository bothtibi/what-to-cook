import streamlit as st

from src.config import DEFAULT_CATEGORIES
from src.recipes import create_recipe, list_recipes, update_recipe


def render_recipes_page():
    st.subheader("Receptek")

    with st.expander("Uj recept felvetele", expanded=False):
        with st.form("create_recipe_form"):
            name = st.text_input("Nev")
            category = st.selectbox("Kategoria", DEFAULT_CATEGORIES)
            tags = st.text_input("Tagek (vesszovel elvalasztva)")
            prep_time_minutes = st.number_input("Elokeszitesi ido (perc)", min_value=0, value=30)
            difficulty = st.text_input("Nehezseg (opcionalis)")
            ingredients_text = st.text_area("Hozzavalok")
            instructions_text = st.text_area("Elkeszites")
            notes_text = st.text_area("Megjegyzes")
            is_favorite = st.checkbox("Kedvenc")
            is_blocked = st.checkbox("Tiltott")
            submitted = st.form_submit_button("Mentes")

        if submitted and name.strip():
            create_recipe(
                {
                    "name": name.strip(),
                    "category": category,
                    "tags": tags,
                    "prep_time_minutes": int(prep_time_minutes),
                    "difficulty": difficulty.strip(),
                    "ingredients_text": ingredients_text.strip(),
                    "instructions_text": instructions_text.strip(),
                    "notes_text": notes_text.strip(),
                    "is_favorite": is_favorite,
                    "is_blocked": is_blocked,
                }
            )
            st.success("Recept letrehozva.")
            st.rerun()

    col1, col2, col3 = st.columns(3)
    query = col1.text_input("Kereses nev szerint")
    filter_category = col2.selectbox("Kategoria szuro", [""] + DEFAULT_CATEGORIES)
    filter_tag = col3.text_input("Tag szuro")
    include_blocked = st.checkbox("Tiltottakat is mutassa", value=True)

    recipes = list_recipes(query=query, category=filter_category, tag=filter_tag, include_blocked=include_blocked)

    if not recipes:
        st.info("Nincs talalat.")
        return

    st.caption(f"Osszesen {len(recipes)} recept")
    for recipe in recipes:
        with st.container(border=True):
            st.markdown(f"### {recipe['name']}")
            st.write(f"Kategoria: {recipe['category']} | Ido: {recipe['prep_time_minutes']} perc")
            if recipe["tags"]:
                st.write(f"Tagek: {recipe['tags']}")
            st.write(recipe["ingredients_text"] or "-")
            st.write(recipe["instructions_text"] or "-")

            with st.expander("Szerkesztes"):
                with st.form(f"edit_recipe_{recipe['id']}"):
                    name = st.text_input("Nev", value=recipe["name"])
                    category = st.selectbox(
                        "Kategoria",
                        DEFAULT_CATEGORIES,
                        index=DEFAULT_CATEGORIES.index(recipe["category"]) if recipe["category"] in DEFAULT_CATEGORIES else 0,
                    )
                    tags = st.text_input("Tagek", value=recipe["tags"])
                    prep_time_minutes = st.number_input(
                        "Elokeszitesi ido (perc)",
                        min_value=0,
                        value=int(recipe["prep_time_minutes"]),
                        key=f"prep_{recipe['id']}",
                    )
                    difficulty = st.text_input("Nehezseg", value=recipe["difficulty"])
                    ingredients_text = st.text_area("Hozzavalok", value=recipe["ingredients_text"])
                    instructions_text = st.text_area("Elkeszites", value=recipe["instructions_text"])
                    notes_text = st.text_area("Megjegyzes", value=recipe["notes_text"])
                    is_favorite = st.checkbox("Kedvenc", value=bool(recipe["is_favorite"]))
                    is_blocked = st.checkbox("Tiltott", value=bool(recipe["is_blocked"]))
                    save = st.form_submit_button("Valtozasok mentese")

                if save and name.strip():
                    update_recipe(
                        recipe["id"],
                        {
                            "name": name.strip(),
                            "category": category,
                            "tags": tags,
                            "prep_time_minutes": int(prep_time_minutes),
                            "difficulty": difficulty.strip(),
                            "ingredients_text": ingredients_text.strip(),
                            "instructions_text": instructions_text.strip(),
                            "notes_text": notes_text.strip(),
                            "is_favorite": is_favorite,
                            "is_blocked": is_blocked,
                        },
                    )
                    st.success("Recept frissitve.")
                    st.rerun()
