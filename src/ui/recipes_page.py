import streamlit as st

from src.config import DEFAULT_CATEGORIES, RECIPE_DIFFICULTIES
from src.recipes import (
    create_recipe,
    list_recipes,
    recipe_name_exists,
    set_dislike_melinda,
    set_dislike_tibi,
    set_favorite_melinda,
    set_favorite_tibi,
    update_recipe,
)


def _tag_chips(tags_text):
    if not tags_text:
        return
    tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
    chips = " ".join(
        [f"<span style='background:#f3f4f6;color:#374151;padding:2px 8px;border-radius:6px;font-size:12px'>{tag}</span>" for tag in tags]
    )
    st.markdown(chips, unsafe_allow_html=True)


def render_recipes_page():
    st.subheader("Receptek")

    with st.expander("Uj recept felvetele", expanded=False):
        with st.form("create_recipe_form"):
            name = st.text_input("Nev")
            category = st.selectbox("Kategoria", DEFAULT_CATEGORIES)
            tags = st.text_input("Tagek (vesszovel elvalasztva)")
            prep_time_minutes = st.number_input("Elokeszitesi ido (perc)", min_value=0, value=30)
            difficulty = st.selectbox("Nehézség", RECIPE_DIFFICULTIES, index=1)
            ingredients_text = st.text_area("Hozzavalok")
            instructions_text = st.text_area("Elkeszites")
            notes_text = st.text_area("Megjegyzes")
            favorite_tibi = st.checkbox("Kedvenc Tibi")
            favorite_melinda = st.checkbox("Kedvenc Melinda")
            dislike_tibi = st.checkbox("Nem szereti Tibi")
            dislike_melinda = st.checkbox("Nem szereti Melinda")
            submitted = st.form_submit_button("Mentes")

        if submitted and name.strip():
            if recipe_name_exists(name):
                st.warning("Mar letezik ilyen nevu recept.")
            else:
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
                        "favorite_tibi": favorite_tibi,
                        "favorite_melinda": favorite_melinda,
                        "dislike_tibi": dislike_tibi,
                        "dislike_melinda": dislike_melinda,
                    }
                )
                st.success("Recept letrehozva.")
                st.rerun()

    col1, col2, col3 = st.columns(3)
    query = col1.text_input("Kereses nev szerint")
    filter_category = col2.selectbox("Kategoria szuro", [""] + DEFAULT_CATEGORIES)
    filter_tag = col3.text_input("Tag szuro")
    include_disliked = st.checkbox("Amit mindketten nem szeretnek is mutassa", value=True)

    recipes = list_recipes(query=query, category=filter_category, tag=filter_tag, include_disliked=include_disliked)

    if not recipes:
        st.info("Nincs talalat.")
        return

    fav_count = sum(1 for recipe in recipes if recipe["favorite_tibi"] or recipe["favorite_melinda"])
    disliked_both_count = sum(1 for recipe in recipes if recipe["dislike_tibi"] and recipe["dislike_melinda"])
    m1, m2, m3 = st.columns(3)
    m1.metric("Osszes recept", len(recipes))
    m2.metric("Kedvencek", fav_count)
    m3.metric("Mindketten nem szeretik", disliked_both_count)

    for recipe in recipes:
        with st.container(border=True):
            head_col1, head_col2 = st.columns([3, 2])
            head_col1.markdown(f"### {recipe['name']}")
            flags = []
            if recipe["favorite_tibi"]:
                flags.append("Kedvenc Tibi")
            if recipe["favorite_melinda"]:
                flags.append("Kedvenc Melinda")
            if recipe["dislike_tibi"]:
                flags.append("Nem szereti Tibi")
            if recipe["dislike_melinda"]:
                flags.append("Nem szereti Melinda")
            suffix = f" | {', '.join(flags)}" if flags else ""
            head_col2.caption(f"{recipe['category']} | {recipe['prep_time_minutes']} perc | {recipe['difficulty']}{suffix}")
            _tag_chips(recipe["tags"])
            st.write(recipe["ingredients_text"] or "-")
            st.write(recipe["instructions_text"] or "-")
            q1, q2 = st.columns(2)
            q3, q4 = st.columns(2)
            if q1.button("Kedvenc Tibi", key=f"fav_tibi_{recipe['id']}"):
                set_favorite_tibi(recipe["id"], not bool(recipe["favorite_tibi"]))
                st.rerun()
            if q2.button("Kedvenc Melinda", key=f"fav_melinda_{recipe['id']}"):
                set_favorite_melinda(recipe["id"], not bool(recipe["favorite_melinda"]))
                st.rerun()
            if q3.button("Nem szereti Tibi", key=f"dis_tibi_{recipe['id']}"):
                set_dislike_tibi(recipe["id"], not bool(recipe["dislike_tibi"]))
                st.rerun()
            if q4.button("Nem szereti Melinda", key=f"dis_melinda_{recipe['id']}"):
                set_dislike_melinda(recipe["id"], not bool(recipe["dislike_melinda"]))
                st.rerun()

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
                    difficulty_options = RECIPE_DIFFICULTIES
                    difficulty = st.selectbox(
                        "Nehézség",
                        difficulty_options,
                        index=difficulty_options.index(recipe["difficulty"]) if recipe["difficulty"] in difficulty_options else 1,
                        key=f"diff_{recipe['id']}",
                    )
                    ingredients_text = st.text_area("Hozzavalok", value=recipe["ingredients_text"])
                    instructions_text = st.text_area("Elkeszites", value=recipe["instructions_text"])
                    notes_text = st.text_area("Megjegyzes", value=recipe["notes_text"])
                    favorite_tibi = st.checkbox("Kedvenc Tibi", value=bool(recipe["favorite_tibi"]), key=f"f1_{recipe['id']}")
                    favorite_melinda = st.checkbox(
                        "Kedvenc Melinda", value=bool(recipe["favorite_melinda"]), key=f"f2_{recipe['id']}"
                    )
                    dislike_tibi = st.checkbox("Nem szereti Tibi", value=bool(recipe["dislike_tibi"]), key=f"d1_{recipe['id']}")
                    dislike_melinda = st.checkbox(
                        "Nem szereti Melinda", value=bool(recipe["dislike_melinda"]), key=f"d2_{recipe['id']}"
                    )
                    save = st.form_submit_button("Valtozasok mentese")

                if save and name.strip():
                    if recipe_name_exists(name, exclude_id=recipe["id"]):
                        st.warning("Mar letezik ilyen nevu recept.")
                    else:
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
                                "favorite_tibi": favorite_tibi,
                                "favorite_melinda": favorite_melinda,
                                "dislike_tibi": dislike_tibi,
                                "dislike_melinda": dislike_melinda,
                            },
                        )
                        st.success("Recept frissitve.")
                        st.rerun()
