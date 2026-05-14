import html
from textwrap import dedent
from datetime import date

import streamlit as st

from src.config import DEFAULT_CATEGORIES
from src.history import add_history_entries, add_history_entry, recent_cooked_dates_by_recipe
from src.i18n import category_label, difficulty_label, t
from src.recipes import get_recipe
from src.recommendations import recommend_meal_combinations, recommend_recipes


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


def _last_cooked_label(recipe, recent_data):
    data = recent_data.get(recipe["id"])
    if not data or not data.get("last_cooked_date"):
        return t("recommendations.last_never")
    try:
        last_date = date.fromisoformat(data["last_cooked_date"])
        days_since = (date.today() - last_date).days
    except (TypeError, ValueError):
        return t("recommendations.last_unknown")

    if days_since == 0:
        return t("recommendations.last_today", date=last_date.isoformat())
    if days_since == 1:
        return t("recommendations.last_yesterday", date=last_date.isoformat())
    return t("recommendations.last_days", days=days_since, date=last_date.isoformat())


def _recipe_line(recipe, recent_data):
    name = html.escape(str(recipe["name"]))
    difficulty = html.escape(difficulty_label(recipe["difficulty"]))
    last_cooked = html.escape(_last_cooked_label(recipe, recent_data))
    return dedent(
        f"""
    <div class="recipe-row">
        <div class="recipe-thumb">{html.escape(_initials(recipe["name"]))}</div>
        <div>
            <div class="recipe-name">{name}</div>
            <div class="recipe-meta">{_category_badge(recipe["category"])} {int(recipe["prep_time_minutes"])} perc
                <span class="difficulty-pill">{difficulty}</span>
            </div>
            <div class="last-cooked">{last_cooked}</div>
        </div>
    </div>
    """
    ).strip()


def _save_history_form(recipe, form_key_prefix, meal_group_id=""):
    with st.form(f"{form_key_prefix}_{recipe['id']}"):
        cooked_date = st.date_input(t("recommendations.cooked_date"), value=date.today(), key=f"date_{form_key_prefix}_{recipe['id']}")
        days_planned = st.number_input(
            t("recommendations.days"),
            min_value=1,
            max_value=14,
            value=1,
            key=f"days_{form_key_prefix}_{recipe['id']}",
        )
        submit = st.form_submit_button(t("recommendations.save"), use_container_width=True)

    if submit:
        add_history_entry(
            recipe_id=recipe["id"],
            cooked_date=str(cooked_date),
            days_planned=int(days_planned),
            quantity_note="",
            meal_group_id=meal_group_id.strip(),
            notes="",
        )
        st.success(t("recommendations.saved"))
        st.rerun()


def _save_combo_history_form(soup_recipe, main_recipe, form_key_prefix, meal_group_id):
    with st.form(form_key_prefix):
        cooked_date = st.date_input(t("recommendations.cooked_date"), value=date.today(), key=f"date_{form_key_prefix}")
        soup_col, main_col = st.columns(2)
        soup_days = soup_col.number_input(
            t("recommendations.soup_days"),
            min_value=1,
            max_value=14,
            value=1,
            key=f"soup_days_{form_key_prefix}",
        )
        main_days = main_col.number_input(
            t("recommendations.main_days"),
            min_value=1,
            max_value=14,
            value=1,
            key=f"main_days_{form_key_prefix}",
        )
        submit = st.form_submit_button(t("recommendations.save"), use_container_width=True)

    if submit:
        common = {
            "cooked_date": str(cooked_date),
            "quantity_note": "",
            "meal_group_id": meal_group_id.strip(),
            "notes": "",
        }
        add_history_entries(
            [
                {"recipe_id": soup_recipe["id"], "days_planned": int(soup_days), **common},
                {"recipe_id": main_recipe["id"], "days_planned": int(main_days), **common},
            ]
        )
        st.success(t("recommendations.combo_saved"))
        st.rerun()


def _render_preview_content(recipe):
    st.caption(f"{category_label(recipe['category'])} · {int(recipe['prep_time_minutes'])} perc · {difficulty_label(recipe['difficulty'])}")
    _tag_chips(recipe["tags"])

    ingredients_tab, instructions_tab = st.tabs([t("common.ingredients"), t("common.instructions")])
    with ingredients_tab:
        st.write(recipe["ingredients_text"] or "-")
    with instructions_tab:
        st.write(recipe["instructions_text"] or "-")

    if st.button(t("recommendations.open_in_recipes"), use_container_width=True):
        st.session_state["active_page"] = "recipes"
        st.session_state["recipe_search"] = recipe["name"]
        st.rerun()


def _render_recipe_preview(recipe_id):
    if not recipe_id:
        return

    recipe = get_recipe(recipe_id)
    if not recipe:
        return

    if hasattr(st, "dialog"):
        @st.dialog(recipe["name"])
        def _dialog():
            _render_preview_content(recipe)

        _dialog()
    else:
        with st.container(border=True):
            st.markdown(f"### {recipe['name']}")
            _render_preview_content(recipe)


def _render_combo_card(combo, idx, recent_data):
    soup_recipe = combo["soup"]["recipe"]
    main_recipe = combo["main"]["recipe"]
    preview_id = None
    st.markdown(
        dedent(
            f"""
        <div class="recommend-card">
            <div class="rank-badge">{idx}</div>
            {_recipe_line(soup_recipe, recent_data)}
            <div class="combo-plus">+</div>
            {_recipe_line(main_recipe, recent_data)}
        </div>
        """
        ).strip(),
        unsafe_allow_html=True,
    )
    detail_cols = st.columns(2)
    if detail_cols[0].button(t("recommendations.soup_details"), key=f"preview_soup_{idx}", use_container_width=True):
        preview_id = soup_recipe["id"]
    if detail_cols[1].button(t("recommendations.main_details"), key=f"preview_main_{idx}", use_container_width=True):
        preview_id = main_recipe["id"]
    meal_group_id = f"combo-{date.today().isoformat()}-{idx}"
    _save_combo_history_form(soup_recipe, main_recipe, f"combo_{idx}", meal_group_id=meal_group_id)
    return preview_id


def _render_single_card(item, idx, recent_data):
    recipe = item["recipe"]
    preview_id = None
    st.markdown(
        dedent(
            f"""
        <div class="recommend-card">
            <div class="rank-badge">{idx}</div>
            {_recipe_line(recipe, recent_data)}
        </div>
        """
        ).strip(),
        unsafe_allow_html=True,
    )
    if st.button(t("common.details"), key=f"preview_single_{idx}_{recipe['id']}", use_container_width=True):
        preview_id = recipe["id"]
    _save_history_form(recipe, f"single_{idx}")
    return preview_id


def render_recommendation_page():
    st.markdown(
        dedent(
            f"""
        <div class="page-panel">
            <h2 style="margin:0;">{t("recommendations.hero_title")}</h2>
            <div class="section-kicker">{t("recommendations.hero_subtitle")}</div>
        </div>
        """,
        ).strip(),
        unsafe_allow_html=True,
    )
    mode_col, category_col, limit_col, refresh_col = st.columns([2.7, 1.8, 1.1, 1.1])
    mode_options = [
        ("combo", t("recommendations.mode_combo")),
        ("soup", t("recommendations.mode_soup")),
        ("main", t("recommendations.mode_main")),
        ("single", t("recommendations.mode_single")),
    ]
    selected_mode_label = mode_col.radio(
        t("recommendations.mode"),
        [label for _, label in mode_options],
        horizontal=True,
        label_visibility="collapsed",
    )
    mode = next(key for key, label in mode_options if label == selected_mode_label)
    category = category_col.selectbox(
        t("recommendations.category"),
        [""] + DEFAULT_CATEGORIES,
        format_func=lambda value: t("category.all") if value == "" else category_label(value),
        label_visibility="collapsed",
    )
    limit = limit_col.selectbox(t("recommendations.count"), [1, 2, 3, 4, 5, 6], index=2, label_visibility="collapsed")
    if refresh_col.button(t("recommendations.refresh"), use_container_width=True):
        st.rerun()
    st.write("")
    recent_data = recent_cooked_dates_by_recipe()

    if mode == "combo":
        combos = recommend_meal_combinations(limit=max(1, min(limit, 6)))
        if not combos:
            st.info(t("recommendations.no_combo"))
            return

        preview_id = None
        for start in range(0, len(combos), 3):
            cols = st.columns(3)
            for offset, combo in enumerate(combos[start : start + 3], start=0):
                with cols[offset]:
                    clicked_preview_id = _render_combo_card(combo, start + offset + 1, recent_data)
                    preview_id = clicked_preview_id or preview_id
        _render_recipe_preview(preview_id)
        return

    if mode == "soup":
        effective_category = "Leves"
    elif mode == "main":
        effective_category = "Főétel"
    else:
        effective_category = category

    recipes = recommend_recipes(category=effective_category, limit=limit)
    if not recipes:
        st.info(t("recommendations.no_recipes"))
        return

    preview_id = None
    for start in range(0, len(recipes), 3):
        cols = st.columns(3)
        for offset, item in enumerate(recipes[start : start + 3], start=0):
            with cols[offset]:
                clicked_preview_id = _render_single_card(item, start + offset + 1, recent_data)
                preview_id = clicked_preview_id or preview_id
    _render_recipe_preview(preview_id)
