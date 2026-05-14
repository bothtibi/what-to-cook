import html
from textwrap import dedent

import streamlit as st

from src.config import DEFAULT_CATEGORIES, RECIPE_DIFFICULTIES
from src.i18n import category_label, difficulty_label, t
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
    return f'<span class="category-pill {_category_class(category)}">{html.escape(category_label(category))}</span>'


def _recipe_list_header(recipe):
    name = html.escape(str(recipe["name"]))
    difficulty = html.escape(difficulty_label(recipe["difficulty"]))
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


PREFERENCE_KEYS = ["neutral", "favorite", "dislike"]


def _preference_label(preference_key):
    return t(f"preferences.{preference_key}")


def _preference_value(is_favorite, is_disliked):
    if is_disliked:
        return "dislike"
    if is_favorite:
        return "favorite"
    return "neutral"


def _preference_flags(tibi_preference, melinda_preference):
    return {
        "favorite_tibi": tibi_preference == "favorite",
        "favorite_melinda": melinda_preference == "favorite",
        "dislike_tibi": tibi_preference == "dislike",
        "dislike_melinda": melinda_preference == "dislike",
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
                f"<span style='background:#fef2f2;color:#991b1b;padding:3px 8px;border-radius:6px;font-size:12px'>{t('preferences.badge_dislike', name=name)}</span>"
            )
        elif is_favorite:
            badges.append(
                f"<span style='background:#fefce8;color:#854d0e;padding:3px 8px;border-radius:6px;font-size:12px'>{t('preferences.badge_favorite', name=name)}</span>"
            )
    if badges:
        st.markdown(" ".join(badges), unsafe_allow_html=True)


def _recipe_form(defaults, form_key, submit_label):
    with st.form(form_key):
        st.markdown(f"##### {t('recipes.form.basic')}")
        top_left, top_right = st.columns([2, 1])
        with top_left:
            name = st.text_input(t("recipes.name"), value=defaults.get("name", ""), key=f"{form_key}_name")
            tags = st.text_input(
                t("recipes.tags"),
                value=defaults.get("tags", ""),
                placeholder=t("recipes.tags_placeholder"),
                key=f"{form_key}_tags",
            )
        with top_right:
            category_value = defaults.get("category", DEFAULT_CATEGORIES[0])
            category = st.selectbox(
                t("recipes.category"),
                DEFAULT_CATEGORIES,
                index=DEFAULT_CATEGORIES.index(category_value) if category_value in DEFAULT_CATEGORIES else 0,
                format_func=category_label,
                key=f"{form_key}_category",
            )
            difficulty_value = defaults.get("difficulty", "Közepes")
            difficulty = st.selectbox(
                t("recipes.difficulty"),
                RECIPE_DIFFICULTIES,
                index=RECIPE_DIFFICULTIES.index(difficulty_value) if difficulty_value in RECIPE_DIFFICULTIES else 1,
                format_func=difficulty_label,
                key=f"{form_key}_difficulty",
            )
            prep_time_minutes = st.number_input(
                t("recipes.prep_time"),
                min_value=0,
                value=int(defaults.get("prep_time_minutes", 30)),
                key=f"{form_key}_prep_time",
            )

        st.markdown(f"##### {t('recipes.form.recipe')}")
        ingredients_text = st.text_area(
            t("common.ingredients"),
            value=defaults.get("ingredients_text", ""),
            height=110,
            key=f"{form_key}_ingredients",
        )
        instructions_text = st.text_area(
            t("common.instructions"),
            value=defaults.get("instructions_text", ""),
            height=140,
            key=f"{form_key}_instructions",
        )

        st.markdown(f"##### {t('recipes.form.preferences')}")
        pref_left, pref_right = st.columns(2)
        tibi_default = _preference_value(defaults.get("favorite_tibi", False), defaults.get("dislike_tibi", False))
        melinda_default = _preference_value(defaults.get("favorite_melinda", False), defaults.get("dislike_melinda", False))
        tibi_preference = pref_left.selectbox(
            "Tibi",
            PREFERENCE_KEYS,
            index=PREFERENCE_KEYS.index(tibi_default),
            format_func=_preference_label,
            key=f"{form_key}_pref_tibi",
        )
        melinda_preference = pref_right.selectbox(
            "Melinda",
            PREFERENCE_KEYS,
            index=PREFERENCE_KEYS.index(melinda_default),
            format_func=_preference_label,
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
        "notes_text": defaults.get("notes_text", "").strip(),
        **_preference_flags(tibi_preference, melinda_preference),
    }
    return submitted, data


def render_recipes_page():
    st.subheader(t("recipes.title"))

    if "show_create_recipe_form" not in st.session_state:
        st.session_state["show_create_recipe_form"] = False
    if st.button(t("recipes.new"), type="primary"):
        st.session_state["show_create_recipe_form"] = not st.session_state["show_create_recipe_form"]
        st.rerun()

    if st.session_state["show_create_recipe_form"]:
        with st.container(border=True):
            st.markdown(f"### {t('recipes.new')}")
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
                t("recipes.save"),
            )

            if submitted and data["name"]:
                if recipe_name_exists(data["name"]):
                    st.warning(t("recipes.exists"))
                else:
                    create_recipe(data)
                    st.success(t("recipes.created"))
                    st.session_state["show_create_recipe_form"] = False
                    st.rerun()

    if "recipe_search" in st.session_state:
        st.session_state["recipe_search_query"] = st.session_state.pop("recipe_search")

    col1, col2, col3 = st.columns(3)
    query = col1.text_input(t("recipes.search"), key="recipe_search_query")
    filter_category = col2.selectbox(
        t("recipes.category_filter"),
        [""] + DEFAULT_CATEGORIES,
        format_func=lambda value: t("category.all") if value == "" else category_label(value),
    )
    filter_tag = col3.text_input(t("recipes.tag_filter"))
    include_disliked = st.checkbox(t("recipes.show_disliked"), value=True)

    recipes = list_recipes(query=query, category=filter_category, tag=filter_tag, include_disliked=include_disliked)

    if not recipes:
        st.info(t("recipes.no_results"))
        return

    fav_count = sum(1 for recipe in recipes if recipe["favorite_tibi"] or recipe["favorite_melinda"])
    disliked_both_count = sum(1 for recipe in recipes if recipe["dislike_tibi"] and recipe["dislike_melinda"])
    m1, m2, m3 = st.columns(3)
    m1.metric(t("recipes.total"), len(recipes))
    m2.metric(t("recipes.favorites"), fav_count)
    m3.metric(t("recipes.disliked_both"), disliked_both_count)

    for recipe in recipes:
        with st.container(border=True):
            _recipe_list_header(recipe)
            _preference_badges(recipe)
            _tag_chips(recipe["tags"])

            with st.expander(t("recipes.details_edit")):
                details_tab, edit_tab = st.tabs([t("common.details"), t("common.edit")])
                with details_tab:
                    left, right = st.columns(2)
                    left.markdown(f"##### {t('common.ingredients')}")
                    left.write(recipe["ingredients_text"] or "-")
                    right.markdown(f"##### {t('common.instructions')}")
                    right.write(recipe["instructions_text"] or "-")

                with edit_tab:
                    save, data = _recipe_form(recipe, f"edit_recipe_{recipe['id']}", t("recipes.save_changes"))

                    if save and data["name"]:
                        if recipe_name_exists(data["name"], exclude_id=recipe["id"]):
                            st.warning(t("recipes.exists"))
                        else:
                            update_recipe(recipe["id"], data)
                            st.success(t("recipes.updated"))
                            st.rerun()
