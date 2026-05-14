import html
from datetime import date

import streamlit as st

from src.config import DEFAULT_CATEGORIES
from src.history import add_history_entries, add_history_entry
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


def _recipe_line(recipe):
    name = html.escape(str(recipe["name"]))
    category = html.escape(str(recipe["category"]))
    difficulty = html.escape(str(recipe["difficulty"]))
    return f"""
    <div class="recipe-row">
        <div class="recipe-thumb">{html.escape(_initials(recipe["name"]))}</div>
        <div>
            <div class="recipe-name">{name}</div>
            <div class="recipe-meta">{category} · {int(recipe["prep_time_minutes"])} perc
                <span class="difficulty-pill">{difficulty}</span>
            </div>
        </div>
    </div>
    """


def _reason_text(reasons):
    if not reasons:
        return "Kiegyensúlyozott választás mára."
    return html.escape(" · ".join(reasons[:2]))


def _save_history_form(recipe, form_key_prefix, meal_group_id=""):
    with st.form(f"{form_key_prefix}_{recipe['id']}"):
        submit = st.form_submit_button("Ezt főzzük", use_container_width=True)

    if submit:
        add_history_entry(
            recipe_id=recipe["id"],
            cooked_date=date.today().isoformat(),
            days_planned=1,
            quantity_note="",
            meal_group_id=meal_group_id.strip(),
            notes="",
        )
        st.success("History bejegyzés mentve.")
        st.rerun()


def _save_combo_history_form(soup_recipe, main_recipe, form_key_prefix, meal_group_id):
    with st.form(form_key_prefix):
        submit = st.form_submit_button("Ezt főzzük", use_container_width=True)

    if submit:
        common = {
            "cooked_date": date.today().isoformat(),
            "days_planned": 1,
            "quantity_note": "",
            "meal_group_id": meal_group_id.strip(),
            "notes": "",
        }
        add_history_entries(
            [
                {"recipe_id": soup_recipe["id"], **common},
                {"recipe_id": main_recipe["id"], **common},
            ]
        )
        st.success("Kombináció history bejegyzés mentve.")
        st.rerun()


def _render_combo_card(combo, idx):
    soup_recipe = combo["soup"]["recipe"]
    main_recipe = combo["main"]["recipe"]
    st.markdown(
        f"""
        <div class="recommend-card">
            <div class="rank-badge">{idx}</div>
            {_recipe_line(soup_recipe)}
            <div class="combo-plus">+</div>
            {_recipe_line(main_recipe)}
            <div class="card-note">{_reason_text(combo["reasons"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    meal_group_id = f"combo-{date.today().isoformat()}-{idx}"
    _save_combo_history_form(soup_recipe, main_recipe, f"combo_{idx}", meal_group_id=meal_group_id)


def _render_single_card(item, idx):
    recipe = item["recipe"]
    st.markdown(
        f"""
        <div class="recommend-card">
            <div class="rank-badge">{idx}</div>
            {_recipe_line(recipe)}
            <div class="card-note">{_reason_text(item["reasons"])}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _save_history_form(recipe, f"single_{idx}")


def render_recommendation_page():
    st.markdown(
        """
        <div class="page-panel">
            <h2 style="margin:0;">Mit főzzünk ma?</h2>
            <div class="section-kicker">Válassz egy ajánlást, vagy kérj új ötleteket.</div>
        </div>
        """,
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

    if mode == "Leves + főétel":
        combos = recommend_meal_combinations(limit=max(1, min(limit, 6)))
        if not combos:
            st.info("Nincs elég leves/főétel recept a kombinációhoz.")
            return

        for start in range(0, len(combos), 3):
            cols = st.columns(3)
            for offset, combo in enumerate(combos[start : start + 3], start=0):
                with cols[offset]:
                    _render_combo_card(combo, start + offset + 1)
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
                _render_single_card(item, start + offset + 1)
