import html
from textwrap import dedent
from datetime import date

import streamlit as st

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
    with st.form(f"{form_key_prefix}_{recipe['id']}", enter_to_submit=False):
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
        st.session_state.pop("cook_modal", None)
        st.session_state["recommendation_notice"] = t("recommendations.saved")
        st.rerun()


def _save_combo_history_form(soup_recipe, main_recipe, form_key_prefix, meal_group_id):
    with st.form(form_key_prefix, enter_to_submit=False):
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
        st.session_state.pop("cook_modal", None)
        st.session_state["recommendation_notice"] = t("recommendations.combo_saved")
        st.rerun()


def _open_single_cook_modal(recipe, idx):
    st.session_state["cook_modal"] = {
        "type": "single",
        "recipe_id": recipe["id"],
        "key": f"single_{idx}_{recipe['id']}",
    }
    st.rerun()


def _open_combo_cook_modal(soup_recipe, main_recipe, idx):
    st.session_state["cook_modal"] = {
        "type": "combo",
        "soup_id": soup_recipe["id"],
        "main_id": main_recipe["id"],
        "meal_group_id": f"combo-{date.today().isoformat()}-{idx}",
        "key": f"combo_{idx}_{soup_recipe['id']}_{main_recipe['id']}",
    }
    st.rerun()


def _render_cook_modal_content(payload):
    if payload["type"] == "combo":
        soup_recipe = get_recipe(payload["soup_id"])
        main_recipe = get_recipe(payload["main_id"])
        if not soup_recipe or not main_recipe:
            st.warning(t("recommendations.no_recipes"))
            return

        st.markdown(f"**{soup_recipe['name']} + {main_recipe['name']}**")
        _save_combo_history_form(
            soup_recipe,
            main_recipe,
            f"cook_modal_{payload['key']}",
            meal_group_id=payload["meal_group_id"],
        )
        return

    recipe = get_recipe(payload["recipe_id"])
    if not recipe:
        st.warning(t("recommendations.no_recipes"))
        return

    st.markdown(f"**{recipe['name']}**")
    _save_history_form(recipe, f"cook_modal_{payload['key']}")


def _render_cook_modal():
    payload = st.session_state.get("cook_modal")
    if not payload:
        return

    if hasattr(st, "dialog"):
        @st.dialog(t("recommendations.save"))
        def _dialog():
            _render_cook_modal_content(payload)

        _dialog()
    else:
        with st.container(border=True):
            st.markdown(f"### {t('recommendations.save')}")
            _render_cook_modal_content(payload)


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
    with st.container(border=True):
        st.markdown(
            dedent(
                f"""
            <div class="recommend-card-content recommend-card-combo">
                <div class="rank-badge">{idx}</div>
                {_recipe_line(soup_recipe, recent_data)}
                <div class="combo-plus">+</div>
                {_recipe_line(main_recipe, recent_data)}
            </div>
            """
            ).strip(),
            unsafe_allow_html=True,
        )
        _, cook_col, _ = st.columns([0.7, 1.35, 0.7])
        if cook_col.button(t("recommendations.save"), key=f"cook_combo_{idx}_{soup_recipe['id']}_{main_recipe['id']}", type="primary", use_container_width=True):
            _open_combo_cook_modal(soup_recipe, main_recipe, idx)
    detail_cols = st.columns(2)
    if detail_cols[0].button(t("recommendations.soup_details"), key=f"preview_soup_{idx}", use_container_width=True):
        st.session_state.pop("cook_modal", None)
        preview_id = soup_recipe["id"]
    if detail_cols[1].button(t("recommendations.main_details"), key=f"preview_main_{idx}", use_container_width=True):
        st.session_state.pop("cook_modal", None)
        preview_id = main_recipe["id"]
    return preview_id


def _render_single_card(item, idx, recent_data):
    recipe = item["recipe"]
    preview_id = None
    with st.container(border=True):
        st.markdown(
            dedent(
                f"""
            <div class="recommend-card-content recommend-card-single">
                <div class="rank-badge">{idx}</div>
                {_recipe_line(recipe, recent_data)}
            </div>
            """
            ).strip(),
            unsafe_allow_html=True,
        )
        _, cook_col, _ = st.columns([0.7, 1.35, 0.7])
        if cook_col.button(t("recommendations.save"), key=f"cook_single_{idx}_{recipe['id']}", type="primary", use_container_width=True):
            _open_single_cook_modal(recipe, idx)
    if st.button(t("common.details"), key=f"preview_single_{idx}_{recipe['id']}", use_container_width=True):
        st.session_state.pop("cook_modal", None)
        preview_id = recipe["id"]
    return preview_id


def _render_mode_picker():
    mode_options = [
        ("combo", t("recommendations.mode_combo")),
        ("soup", t("recommendations.mode_soup")),
        ("main", t("recommendations.mode_main")),
        ("single", t("recommendations.mode_single")),
    ]
    if st.session_state.get("recommendation_mode") not in {key for key, _ in mode_options}:
        st.session_state["recommendation_mode"] = "combo"

    st.caption(t("recommendations.mode"))
    cols = st.columns(len(mode_options))
    for col, (mode_key, label) in zip(cols, mode_options):
        active = st.session_state["recommendation_mode"] == mode_key
        if col.button(label, key=f"recommendation_mode_{mode_key}", type="primary" if active else "secondary", use_container_width=True):
            st.session_state["recommendation_mode"] = mode_key
            st.rerun()
    return st.session_state["recommendation_mode"]


def _render_count_picker():
    if not isinstance(st.session_state.get("recommendation_limit"), int):
        st.session_state["recommendation_limit"] = 3
    if st.session_state.get("recommendation_limit") not in range(1, 7):
        st.session_state["recommendation_limit"] = 3

    return int(
        st.number_input(
            t("recommendations.count"),
            min_value=1,
            max_value=6,
            step=1,
            key="recommendation_limit",
            width=96,
        )
    )


def _render_max_prep_time_picker():
    if not isinstance(st.session_state.get("recommendation_max_prep_time"), int):
        st.session_state["recommendation_max_prep_time"] = 90
    if st.session_state.get("recommendation_max_prep_time") not in range(0, 501):
        st.session_state["recommendation_max_prep_time"] = 90

    return int(
        st.number_input(
            t("recommendations.max_prep_time"),
            min_value=0,
            max_value=500,
            step=10,
            key="recommendation_max_prep_time",
            width=150,
        )
    )


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
    mode_area, count_area, prep_time_area, refresh_area = st.columns([5.2, 0.9, 1.45, 1.25], vertical_alignment="bottom")
    with mode_area:
        mode = _render_mode_picker()
    with count_area:
        limit = _render_count_picker()
    with prep_time_area:
        max_prep_time = _render_max_prep_time_picker()
    with refresh_area:
        refresh_clicked = st.button(t("recommendations.refresh"), use_container_width=True)
    if refresh_clicked:
        st.rerun()
    if st.session_state.get("recommendation_notice"):
        st.success(st.session_state.pop("recommendation_notice"))
    st.write("")
    recent_data = recent_cooked_dates_by_recipe()

    if mode == "combo":
        combos = recommend_meal_combinations(limit=max(1, min(limit, 6)), max_prep_time=max_prep_time)
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
        _render_cook_modal()
        return

    if mode == "soup":
        effective_category = "Leves"
    elif mode == "main":
        effective_category = "Főétel"
    else:
        effective_category = ""

    recipes = recommend_recipes(category=effective_category, limit=limit, max_prep_time=max_prep_time)
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
    _render_cook_modal()
