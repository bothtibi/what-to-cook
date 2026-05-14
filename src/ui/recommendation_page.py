import html
from textwrap import dedent
from datetime import date

import streamlit as st

from src.config import DEFAULT_CATEGORIES
from src.history import add_history_entries, add_history_entry, recent_cooked_dates_by_recipe
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
    return f'<span class="category-pill {_category_class(category)}">{html.escape(str(category))}</span>'


def _last_cooked_label(recipe, recent_data):
    data = recent_data.get(recipe["id"])
    if not data or not data.get("last_cooked_date"):
        return "Utoljára: még nem volt főzve"
    try:
        last_date = date.fromisoformat(data["last_cooked_date"])
        days_since = (date.today() - last_date).days
    except (TypeError, ValueError):
        return "Utoljára: ismeretlen"

    if days_since == 0:
        return f"Utoljára: ma ({last_date.isoformat()})"
    if days_since == 1:
        return f"Utoljára: tegnap ({last_date.isoformat()})"
    return f"Utoljára: {days_since} napja ({last_date.isoformat()})"


def _recipe_line(recipe, recent_data):
    name = html.escape(str(recipe["name"]))
    difficulty = html.escape(str(recipe["difficulty"]))
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
        cooked_date = st.date_input("Mikor főztétek?", value=date.today(), key=f"date_{form_key_prefix}_{recipe['id']}")
        days_planned = st.number_input(
            "Hány napra?",
            min_value=1,
            max_value=14,
            value=1,
            key=f"days_{form_key_prefix}_{recipe['id']}",
        )
        submit = st.form_submit_button("Ezt főzzük", use_container_width=True)

    if submit:
        add_history_entry(
            recipe_id=recipe["id"],
            cooked_date=str(cooked_date),
            days_planned=int(days_planned),
            quantity_note="",
            meal_group_id=meal_group_id.strip(),
            notes="",
        )
        st.success("History bejegyzés mentve.")
        st.rerun()


def _save_combo_history_form(soup_recipe, main_recipe, form_key_prefix, meal_group_id):
    with st.form(form_key_prefix):
        cooked_date = st.date_input("Mikor főztétek?", value=date.today(), key=f"date_{form_key_prefix}")
        soup_col, main_col = st.columns(2)
        soup_days = soup_col.number_input(
            "Leves hány napra?",
            min_value=1,
            max_value=14,
            value=1,
            key=f"soup_days_{form_key_prefix}",
        )
        main_days = main_col.number_input(
            "Főétel hány napra?",
            min_value=1,
            max_value=14,
            value=1,
            key=f"main_days_{form_key_prefix}",
        )
        submit = st.form_submit_button("Ezt főzzük", use_container_width=True)

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
        st.success("Kombináció history bejegyzés mentve.")
        st.rerun()


def _open_recipe_preview(recipe_id):
    st.session_state["recipe_preview_id"] = recipe_id


def _render_preview_content(recipe):
    st.caption(f"{recipe['category']} · {int(recipe['prep_time_minutes'])} perc · {recipe['difficulty']}")
    _tag_chips(recipe["tags"])

    ingredients_tab, instructions_tab, notes_tab = st.tabs(["Hozzávalók", "Elkészítés", "Megjegyzés"])
    with ingredients_tab:
        st.write(recipe["ingredients_text"] or "-")
    with instructions_tab:
        st.write(recipe["instructions_text"] or "-")
    with notes_tab:
        st.write(recipe["notes_text"] or "-")

    col1, col2 = st.columns(2)
    if col1.button("Megnyitás a receptek között", use_container_width=True):
        st.session_state["active_page"] = "Receptek"
        st.session_state["recipe_search"] = recipe["name"]
        st.session_state.pop("recipe_preview_id", None)
        st.rerun()
    if col2.button("Bezárás", use_container_width=True):
        st.session_state.pop("recipe_preview_id", None)
        st.rerun()


def _render_recipe_preview():
    recipe_id = st.session_state.get("recipe_preview_id")
    if not recipe_id:
        return

    recipe = get_recipe(recipe_id)
    if not recipe:
        st.session_state.pop("recipe_preview_id", None)
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
    if detail_cols[0].button("Leves részletei", key=f"preview_soup_{idx}", use_container_width=True):
        _open_recipe_preview(soup_recipe["id"])
    if detail_cols[1].button("Főétel részletei", key=f"preview_main_{idx}", use_container_width=True):
        _open_recipe_preview(main_recipe["id"])
    meal_group_id = f"combo-{date.today().isoformat()}-{idx}"
    _save_combo_history_form(soup_recipe, main_recipe, f"combo_{idx}", meal_group_id=meal_group_id)


def _render_single_card(item, idx, recent_data):
    recipe = item["recipe"]
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
    if st.button("Részletek", key=f"preview_single_{idx}_{recipe['id']}", use_container_width=True):
        _open_recipe_preview(recipe["id"])
    _save_history_form(recipe, f"single_{idx}")


def render_recommendation_page():
    st.markdown(
        dedent(
            """
        <div class="page-panel">
            <h2 style="margin:0;">Mit főzzünk ma?</h2>
            <div class="section-kicker">Válassz egy ajánlást, vagy kérj új ötleteket.</div>
        </div>
        """,
        ).strip(),
        unsafe_allow_html=True,
    )
    mode_col, category_col, limit_col, refresh_col = st.columns([2.7, 1.8, 1.1, 1.1])
    mode = mode_col.radio(
        "Mód",
        ["Leves + főétel", "Csak leves", "Csak főétel", "Csak recept"],
        horizontal=True,
        label_visibility="collapsed",
    )
    category = category_col.selectbox("Kategória", [""] + DEFAULT_CATEGORIES, label_visibility="collapsed")
    limit = limit_col.selectbox("Darab", [1, 2, 3, 4, 5, 6], index=2, label_visibility="collapsed")
    if refresh_col.button("Új javaslatok", use_container_width=True):
        st.rerun()
    st.write("")
    recent_data = recent_cooked_dates_by_recipe()

    if mode == "Leves + főétel":
        combos = recommend_meal_combinations(limit=max(1, min(limit, 6)))
        if not combos:
            st.info("Nincs elég leves/főétel recept a kombinációhoz.")
            return

        for start in range(0, len(combos), 3):
            cols = st.columns(3)
            for offset, combo in enumerate(combos[start : start + 3], start=0):
                with cols[offset]:
                    _render_combo_card(combo, start + offset + 1, recent_data)
        _render_recipe_preview()
        return

    if mode == "Csak leves":
        effective_category = "Leves"
    elif mode == "Csak főétel":
        effective_category = "Főétel"
    else:
        effective_category = category

    recipes = recommend_recipes(category=effective_category, limit=limit)
    if not recipes:
        st.info("Nincs ajánlható recept. Ellenőrizd a receptlistát vagy a szűrőket.")
        return

    for start in range(0, len(recipes), 3):
        cols = st.columns(3)
        for offset, item in enumerate(recipes[start : start + 3], start=0):
            with cols[offset]:
                _render_single_card(item, start + offset + 1, recent_data)
    _render_recipe_preview()
