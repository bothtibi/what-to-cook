import html
from textwrap import dedent

import streamlit as st

from src.config import DEFAULT_CATEGORIES, RECIPE_DIFFICULTIES
from src.recipes import (
    create_recipe,
    list_recipes,
    recipe_name_exists,
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


def _initials(name):
    words = [word for word in str(name).split() if word]
    if not words:
        return "R"
    return "".join(word[0] for word in words[:2])


def _category_class(category):
    normalized = str(category).strip().lower()
    mapping = {
        "leves": "category-leves",
        "főétel": "category-foetel",
        "foetel": "category-foetel",
        "reggeli": "category-reggeli",
        "vacsora": "category-vacsora",
    }
    return mapping.get(normalized, "category-other")


def _category_badge(category):
    return f'<span class="category-pill {_category_class(category)}">{html.escape(str(category))}</span>'


def _recipe_list_header(recipe):
    name = html.escape(str(recipe["name"]))
    difficulty = html.escape(str(recipe["difficulty"]))
    initials = html.escape(_initials(recipe["name"]))
    st.markdown(
        dedent(
            f"""
        <div class="list-row">
            <div class="recipe-row" style="margin:0;">
                <div class="recipe-thumb">{initials}</div>
                <div>
                    <div class="recipe-name">{name}</div>
                    <div class="recipe-meta">{_category_badge(recipe["category"])} {int(recipe["prep_time_minutes"])} perc
                        <span class="difficulty-pill">{difficulty}</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        ).strip(),
        unsafe_allow_html=True,
    )


PREFERENCE_OPTIONS = ["Semleges", "Kedvenc", "Nem szereti"]


def _preference_value(is_favorite, is_disliked):
    if is_disliked:
        return "Nem szereti"
    if is_favorite:
        return "Kedvenc"
    return "Semleges"


def _preference_flags(tibi_preference, melinda_preference):
    return {
        "favorite_tibi": tibi_preference == "Kedvenc",
        "favorite_melinda": melinda_preference == "Kedvenc",
        "dislike_tibi": tibi_preference == "Nem szereti",
        "dislike_melinda": melinda_preference == "Nem szereti",
    }


def _preference_badges(recipe):
    badges = []
    people = [
        ("Tibi", recipe["favorite_tibi"], recipe["dislike_tibi"]),
        ("Melinda", recipe["favorite_melinda"], recipe["dislike_melinda"]),
    ]
    for name, is_favorite, is_disliked in people:
        if is_disliked:
            badges.append(
                f"<span style='background:#fef2f2;color:#991b1b;padding:3px 8px;border-radius:6px;font-size:12px'>{name}: nem szereti</span>"
            )
        elif is_favorite:
            badges.append(
                f"<span style='background:#fefce8;color:#854d0e;padding:3px 8px;border-radius:6px;font-size:12px'>{name}: kedvenc</span>"
            )
    if badges:
        st.markdown(" ".join(badges), unsafe_allow_html=True)


def _recipe_form(defaults, form_key, submit_label):
    with st.form(form_key):
        st.markdown("##### Alapadatok")
        top_left, top_right = st.columns([2, 1])
        with top_left:
            name = st.text_input("Név", value=defaults.get("name", ""), key=f"{form_key}_name")
            tags = st.text_input(
                "Tagek",
                value=defaults.get("tags", ""),
                placeholder="gyors, húsos, téli",
                key=f"{form_key}_tags",
            )
        with top_right:
            category_value = defaults.get("category", DEFAULT_CATEGORIES[0])
            category = st.selectbox(
                "Kategória",
                DEFAULT_CATEGORIES,
                index=DEFAULT_CATEGORIES.index(category_value) if category_value in DEFAULT_CATEGORIES else 0,
                key=f"{form_key}_category",
            )
            difficulty_value = defaults.get("difficulty", "Közepes")
            difficulty = st.selectbox(
                "Nehézség",
                RECIPE_DIFFICULTIES,
                index=RECIPE_DIFFICULTIES.index(difficulty_value) if difficulty_value in RECIPE_DIFFICULTIES else 1,
                key=f"{form_key}_difficulty",
            )
            prep_time_minutes = st.number_input(
                "Előkészítési idő (perc)",
                min_value=0,
                value=int(defaults.get("prep_time_minutes", 30)),
                key=f"{form_key}_prep_time",
            )

        st.markdown("##### Recept")
        ingredients_text = st.text_area(
            "Hozzávalók",
            value=defaults.get("ingredients_text", ""),
            height=110,
            key=f"{form_key}_ingredients",
        )
        instructions_text = st.text_area(
            "Elkészítés",
            value=defaults.get("instructions_text", ""),
            height=140,
            key=f"{form_key}_instructions",
        )
        notes_text = st.text_area(
            "Megjegyzés",
            value=defaults.get("notes_text", ""),
            height=80,
            key=f"{form_key}_notes",
        )

        st.markdown("##### Ízlések")
        pref_left, pref_right = st.columns(2)
        tibi_default = _preference_value(defaults.get("favorite_tibi", False), defaults.get("dislike_tibi", False))
        melinda_default = _preference_value(defaults.get("favorite_melinda", False), defaults.get("dislike_melinda", False))
        tibi_preference = pref_left.selectbox(
            "Tibi",
            PREFERENCE_OPTIONS,
            index=PREFERENCE_OPTIONS.index(tibi_default),
            key=f"{form_key}_pref_tibi",
        )
        melinda_preference = pref_right.selectbox(
            "Melinda",
            PREFERENCE_OPTIONS,
            index=PREFERENCE_OPTIONS.index(melinda_default),
            key=f"{form_key}_pref_melinda",
        )

        submitted = st.form_submit_button(submit_label)

    data = {
        "name": name.strip(),
        "category": category,
        "tags": tags,
        "prep_time_minutes": int(prep_time_minutes),
        "difficulty": difficulty.strip(),
        "ingredients_text": ingredients_text.strip(),
        "instructions_text": instructions_text.strip(),
        "notes_text": notes_text.strip(),
        **_preference_flags(tibi_preference, melinda_preference),
    }
    return submitted, data


def render_recipes_page():
    st.subheader("Receptek")

    with st.expander("Új recept felvétele", expanded=False):
        submitted, data = _recipe_form(
            {
                "name": "",
                "category": DEFAULT_CATEGORIES[0],
                "tags": "",
                "prep_time_minutes": 30,
                "difficulty": "Közepes",
                "ingredients_text": "",
                "instructions_text": "",
                "notes_text": "",
                "favorite_tibi": False,
                "favorite_melinda": False,
                "dislike_tibi": False,
                "dislike_melinda": False,
            },
            "create_recipe_form",
            "Recept mentése",
        )

        if submitted and data["name"]:
            if recipe_name_exists(data["name"]):
                st.warning("Mar letezik ilyen nevu recept.")
            else:
                create_recipe(data)
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
            _recipe_list_header(recipe)
            _preference_badges(recipe)
            _tag_chips(recipe["tags"])

            with st.expander("Részletek és szerkesztés"):
                details_tab, edit_tab = st.tabs(["Részletek", "Szerkesztés"])
                with details_tab:
                    left, right = st.columns(2)
                    left.markdown("##### Hozzávalók")
                    left.write(recipe["ingredients_text"] or "-")
                    right.markdown("##### Elkészítés")
                    right.write(recipe["instructions_text"] or "-")
                    if recipe["notes_text"]:
                        st.markdown("##### Megjegyzés")
                        st.write(recipe["notes_text"])

                with edit_tab:
                    save, data = _recipe_form(recipe, f"edit_recipe_{recipe['id']}", "Változások mentése")

                    if save and data["name"]:
                        if recipe_name_exists(data["name"], exclude_id=recipe["id"]):
                            st.warning("Mar letezik ilyen nevu recept.")
                        else:
                            update_recipe(recipe["id"], data)
                            st.success("Recept frissitve.")
                            st.rerun()
