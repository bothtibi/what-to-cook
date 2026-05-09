from datetime import date

import streamlit as st

from src.config import DEFAULT_CATEGORIES
from src.history import add_history_entry
from src.recommendations import recommend_meal_combinations, recommend_recipes


def _tag_chips(tags_text):
    if not tags_text:
        return
    tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
    chips = " ".join(
        [f"<span style='background:#eef2ff;color:#4338ca;padding:2px 8px;border-radius:999px;font-size:12px'>{tag}</span>" for tag in tags]
    )
    st.markdown(chips, unsafe_allow_html=True)


def _save_history_form(recipe, form_key_prefix, meal_group_id=""):
    with st.form(f"{form_key_prefix}_{recipe['id']}"):
        st.caption("Ezt megfoztuk")
        cooked_date = st.date_input("Mikor?", value=date.today(), key=f"date_{form_key_prefix}_{recipe['id']}")
        days_planned = st.number_input(
            "Hany napra fozve?",
            min_value=1,
            max_value=14,
            value=1,
            key=f"days_{form_key_prefix}_{recipe['id']}",
        )
        quantity_note = st.text_input("Mennyiseg roviden", key=f"qty_{form_key_prefix}_{recipe['id']}")
        notes = st.text_area("Megjegyzes", key=f"note_{form_key_prefix}_{recipe['id']}")
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


def render_recommendation_page():
    st.subheader("Mit fozzunk?")
    mode_col, col1, col2 = st.columns([2, 2, 1])
    mode = mode_col.selectbox(
        "Mod",
        ["csak recept", "csak leves", "csak foetel", "leves + foetel"],
    )
    category = col1.selectbox("Kategoria (opcionalis)", [""] + DEFAULT_CATEGORIES)
    limit = col2.slider("Hany ajanlat legyen?", min_value=1, max_value=10, value=5)

    if mode == "leves + foetel":
        combos = recommend_meal_combinations(limit=max(1, min(limit, 6)))
        if not combos:
            st.info("Nincs eleg leves/foetel recept a kombinaciohoz.")
            return

        st.metric("Kombinaciok", len(combos))
        for idx, combo in enumerate(combos, start=1):
            soup_recipe = combo["soup"]["recipe"]
            main_recipe = combo["main"]["recipe"]
            meal_group_id = f"combo-{date.today().isoformat()}-{idx}"
            with st.container(border=True):
                st.markdown(f"### #{idx} kombinacio")
                left, right = st.columns(2)
                with left:
                    st.markdown(f"**Leves:** {soup_recipe['name']}")
                    st.caption(f"{soup_recipe['prep_time_minutes']} perc")
                    _tag_chips(soup_recipe["tags"])
                with right:
                    st.markdown(f"**Foetel:** {main_recipe['name']}")
                    st.caption(f"{main_recipe['prep_time_minutes']} perc")
                    _tag_chips(main_recipe["tags"])

                st.caption("Ajanlas oka: " + " | ".join(combo["reasons"]))
                c1, c2 = st.columns(2)
                with c1:
                    _save_history_form(soup_recipe, f"combo_soup_{idx}", meal_group_id=meal_group_id)
                with c2:
                    _save_history_form(main_recipe, f"combo_main_{idx}", meal_group_id=meal_group_id)
        return

    if mode == "csak leves":
        effective_category = "leves"
    elif mode == "csak foetel":
        effective_category = "foetel"
    else:
        effective_category = category

    recipes = recommend_recipes(category=effective_category, limit=limit)
    if not recipes:
        st.info("Nincs ajanlhato recept. Ellenorizd a receptlistat vagy a szuroket.")
        return

    stat1, stat2 = st.columns(2)
    stat1.metric("Javaslatok", len(recipes))
    stat2.metric("Aktiv kategoria", effective_category or "mind")

    for item in recipes:
        recipe = item["recipe"]
        with st.container(border=True):
            top_col1, top_col2 = st.columns([3, 2])
            top_col1.markdown(f"### {recipe['name']}")
            top_col2.caption(f"Kategoria: {recipe['category']} | Ido: {recipe['prep_time_minutes']} perc")
            _tag_chips(recipe["tags"])
            if item["reasons"]:
                st.caption("Ajanlas oka: " + " | ".join(item["reasons"]))
            st.write(recipe["ingredients_text"] or "-")
            _save_history_form(recipe, "single")
