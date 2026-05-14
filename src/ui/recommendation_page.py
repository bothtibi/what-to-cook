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


def _save_combo_history_form(soup_recipe, main_recipe, form_key_prefix, meal_group_id):
    with st.form(form_key_prefix):
        st.caption("Ezt a kombinaciot megfoztuk")
        cooked_date = st.date_input("Mikor?", value=date.today(), key=f"date_{form_key_prefix}")
        days_planned = st.number_input(
            "Hany napra fozve?",
            min_value=1,
            max_value=14,
            value=1,
            key=f"days_{form_key_prefix}",
        )
        quantity_note = st.text_input("Mennyiseg roviden", key=f"qty_{form_key_prefix}")
        notes = st.text_area("Megjegyzes", key=f"note_{form_key_prefix}")
        submit = st.form_submit_button("Kombinacio mentese a history-ba")

    if submit:
        common = {
            "cooked_date": str(cooked_date),
            "days_planned": int(days_planned),
            "quantity_note": quantity_note.strip(),
            "meal_group_id": meal_group_id.strip(),
            "notes": notes.strip(),
        }
        add_history_entries(
            [
                {"recipe_id": soup_recipe["id"], **common},
                {"recipe_id": main_recipe["id"], **common},
            ]
        )
        st.success("Kombinacio history bejegyzes mentve.")
        st.rerun()


def render_recommendation_page():
    st.subheader("Mit főzzünk?")
    mode_col, col1, col2 = st.columns([2.2, 2, 1.2])
    mode = mode_col.selectbox(
        "Mód",
        ["Csak recept", "Csak leves", "Csak főétel", "Leves + főétel"],
    )
    category = col1.selectbox("Kategória (opcionális)", [""] + DEFAULT_CATEGORIES)
    limit = col2.selectbox("Ajánlatok száma", [1, 2, 3, 4, 5, 6], index=2)

    if mode == "Leves + főétel":
        combos = recommend_meal_combinations(limit=max(1, min(limit, 6)))
        if not combos:
            st.info("Nincs elég leves/főétel recept a kombinációhoz.")
            return

        st.metric("Kombinációk", len(combos))
        for idx, combo in enumerate(combos, start=1):
            soup_recipe = combo["soup"]["recipe"]
            main_recipe = combo["main"]["recipe"]
            meal_group_id = f"combo-{date.today().isoformat()}-{idx}"
            with st.container(border=True):
                st.markdown(f"### #{idx} kombináció")
                left, right = st.columns(2)
                with left:
                    st.markdown(f"**Leves:** {soup_recipe['name']}")
                    st.caption(f"{soup_recipe['prep_time_minutes']} perc")
                    _tag_chips(soup_recipe["tags"])
                with right:
                    st.markdown(f"**Főétel:** {main_recipe['name']}")
                    st.caption(f"{main_recipe['prep_time_minutes']} perc")
                    _tag_chips(main_recipe["tags"])

                st.caption("Ajánlás oka: " + " | ".join(combo["reasons"]))
                _save_combo_history_form(soup_recipe, main_recipe, f"combo_{idx}", meal_group_id=meal_group_id)
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

    stat1, stat2 = st.columns(2)
    stat1.metric("Javaslatok", len(recipes))
    stat2.metric("Aktív kategória", effective_category or "Mind")

    for item in recipes:
        recipe = item["recipe"]
        with st.container(border=True):
            top_col1, top_col2 = st.columns([3, 2])
            top_col1.markdown(f"### {recipe['name']}")
            top_col2.caption(f"Kategória: {recipe['category']} | Idő: {recipe['prep_time_minutes']} perc")
            _tag_chips(recipe["tags"])
            if item["reasons"]:
                st.caption("Ajánlás oka: " + " | ".join(item["reasons"]))
            st.write(recipe["ingredients_text"] or "-")
            _save_history_form(recipe, "single")
