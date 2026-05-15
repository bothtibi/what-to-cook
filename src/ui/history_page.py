import html
from textwrap import dedent
from datetime import date, datetime, timedelta

import streamlit as st

from src.history import (
    add_history_entries,
    add_history_entry,
    delete_history_entry,
    delete_history_group,
    list_history,
    update_history_entry,
)
from src.i18n import category_label, t
from src.recipes import list_recipes


def _group_by_day(entries):
    grouped = {}
    for item in entries:
        grouped.setdefault(item["cooked_date"], []).append(item)
    return grouped


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


def _combo_badge():
    return f'<span class="combo-pill">{t("history.combo")}</span>'


def _matches_category(recipe, category_key):
    category = str(recipe["category"]).strip().casefold()
    if category_key == "soup":
        return category == "leves"
    if category_key == "main":
        return category in {"foetel", "f\u0151\u00e9tel"}
    return False


def _recipe_lookup_options(recipes):
    options = {}
    for recipe in recipes:
        label = f"{recipe['name']} - {category_label(recipe['category'])}"
        if label in options:
            label = f"{label} #{recipe['id']}"
        options[label] = recipe
    return options


def _select_recipe(label, recipes, key):
    options = _recipe_lookup_options(recipes)
    selected_label = st.selectbox(label, list(options.keys()), key=key)
    return options[selected_label]


def _parse_history_date(value):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return date.today()


def _render_manual_add():
    recipes = list_recipes(include_disliked=True)

    if "show_manual_history_form" not in st.session_state:
        st.session_state["show_manual_history_form"] = False

    if st.session_state.get("manual_history_notice"):
        st.success(st.session_state.pop("manual_history_notice"))

    if st.button(t("history.manual_add"), type="primary"):
        st.session_state["show_manual_history_form"] = not st.session_state["show_manual_history_form"]
        st.rerun()

    if not st.session_state["show_manual_history_form"]:
        return

    with st.container(border=True):
        if not recipes:
            st.info(t("history.no_recipes_to_add"))
            return

        add_type_options = {
            t("history.add_single"): "single",
            t("history.add_combo"): "combo",
        }
        selected_type = st.selectbox(t("history.add_type"), list(add_type_options.keys()))
        add_type = add_type_options[selected_type]

        with st.form("manual_history_add"):
            cooked_date = st.date_input(t("history.cooked_date"), value=date.today())

            if add_type == "combo":
                soups = [recipe for recipe in recipes if _matches_category(recipe, "soup")] or recipes
                mains = [recipe for recipe in recipes if _matches_category(recipe, "main")] or recipes
                soup_recipe = _select_recipe(t("history.soup_recipe"), soups, "manual_history_soup")
                main_recipe = _select_recipe(t("history.main_recipe"), mains, "manual_history_main")
                soup_days_col, main_days_col = st.columns(2)
                soup_days = soup_days_col.number_input(
                    t("history.soup_days"),
                    min_value=1,
                    max_value=14,
                    value=1,
                    step=1,
                )
                main_days = main_days_col.number_input(
                    t("history.main_days"),
                    min_value=1,
                    max_value=14,
                    value=1,
                    step=1,
                )
            else:
                recipe = _select_recipe(t("history.recipe"), recipes, "manual_history_recipe")
                days = st.number_input(
                    t("history.days"),
                    min_value=1,
                    max_value=14,
                    value=1,
                    step=1,
                )

            quantity_note = st.text_input(t("history.quantity_note"))
            notes = st.text_area(t("history.notes"), height=80)
            submitted = st.form_submit_button(t("history.save_entry"), use_container_width=True)

    if not submitted:
        return

    cooked_date_value = cooked_date.isoformat()

    if add_type == "combo":
        meal_group_id = f"manual-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        add_history_entries(
            [
                {
                    "recipe_id": soup_recipe["id"],
                    "cooked_date": cooked_date_value,
                    "days_planned": int(soup_days),
                    "quantity_note": quantity_note.strip(),
                    "meal_group_id": meal_group_id,
                    "notes": notes.strip(),
                },
                {
                    "recipe_id": main_recipe["id"],
                    "cooked_date": cooked_date_value,
                    "days_planned": int(main_days),
                    "quantity_note": quantity_note.strip(),
                    "meal_group_id": meal_group_id,
                    "notes": notes.strip(),
                },
            ]
        )
        st.session_state["manual_history_notice"] = t("history.saved_combo")
    else:
        add_history_entry(
            recipe["id"],
            cooked_date_value,
            int(days),
            quantity_note.strip(),
            "",
            notes.strip(),
        )
        st.session_state["manual_history_notice"] = t("history.saved_entry")
    st.session_state["show_manual_history_form"] = False
    st.rerun()


def _entry_details(item):
    details = [t("history.days_planned", days=int(item["days_planned"]))]
    if item["quantity_note"]:
        details.append(t("history.quantity", value=item["quantity_note"]))
    if item["notes"]:
        details.append(t("history.note", value=item["notes"]))
    if item["meal_group_id"]:
        details.append(t("history.combo_part"))
    return " · ".join(details)


def _render_entry_card(item):
    st.markdown(
        dedent(
            f"""
        <div class="history-entry">
            <div class="history-title">{html.escape(str(item["recipe_name"]))}</div>
            <div class="history-meta">
                {_category_badge(item["category"])}
                {html.escape(_entry_details(item))}
            </div>
        </div>
        """,
        ).strip(),
        unsafe_allow_html=True,
    )


def _render_entry_action_fields(item, suffix=""):
    action_key = f"history_action_{item['id']}_{suffix}"
    with st.form(f"edit_history_{item['id']}_{suffix}"):
        cooked_date = st.date_input(
            t("history.cooked_date"),
            value=_parse_history_date(item["cooked_date"]),
            key=f"history_date_{item['id']}_{suffix}",
        )
        days_planned = st.number_input(
            t("history.days"),
            min_value=1,
            max_value=14,
            value=int(item["days_planned"]),
            step=1,
            key=f"history_days_{item['id']}_{suffix}",
        )
        quantity_note = st.text_input(
            t("history.quantity_note"),
            value=item["quantity_note"],
            key=f"history_quantity_{item['id']}_{suffix}",
        )
        notes = st.text_area(
            t("history.notes"),
            value=item["notes"],
            height=70,
            key=f"history_notes_{item['id']}_{suffix}",
        )
        saved = st.form_submit_button(t("history.save_changes"), use_container_width=True)

    if saved:
        update_history_entry(item["id"], cooked_date.isoformat(), int(days_planned), quantity_note, notes)
        st.success(t("history.updated"))
        st.rerun()

    confirm_delete = st.checkbox(t("history.delete_confirm"), key=f"confirm_delete_{action_key}")
    if st.button(t("history.delete_entry"), key=f"delete_{action_key}", disabled=not confirm_delete):
        delete_history_entry(item["id"])
        st.success(t("history.deleted"))
        st.rerun()


def _render_entry_actions(item, suffix=""):
    with st.expander(t("history.manage_entry")):
        _render_entry_action_fields(item, suffix)


def _render_combo_card(items, suffix=""):
    recipe_names = " + ".join(html.escape(str(item["recipe_name"])) for item in items)
    badges = " ".join(_category_badge(item["category"]) for item in items)
    day_parts = [
        f"{item['recipe_name']}: {t('history.days_planned', days=int(item['days_planned']))}"
        for item in items
    ]
    notes = [str(item["notes"]).strip() for item in items if item["notes"]]
    note_text = f" · {html.escape(t('history.note', value=' | '.join(notes)))}" if notes else ""

    st.markdown(
        dedent(
            f"""
        <div class="history-entry history-combo">
            <div class="history-title">{_combo_badge()} {recipe_names}</div>
            <div class="history-meta">{badges} {html.escape(" · ".join(day_parts))}{note_text}</div>
        </div>
        """,
        ).strip(),
        unsafe_allow_html=True,
    )
    with st.expander(t("history.manage_combo")):
        for item in items:
            st.markdown(f"**{html.escape(str(item['recipe_name']))}**")
            _render_entry_action_fields(item, suffix=f"combo_{suffix}")

        if items and items[0]["meal_group_id"]:
            group_key = f"{items[0]['meal_group_id']}_{suffix}"
            confirm_delete = st.checkbox(t("history.delete_combo_confirm"), key=f"confirm_delete_combo_{group_key}")
            if st.button(
                t("history.delete_combo"),
                key=f"delete_combo_{group_key}",
                disabled=not confirm_delete,
            ):
                delete_history_group(items[0]["meal_group_id"])
                st.success(t("history.deleted_combo"))
                st.rerun()


def _split_grouped_items(items):
    combo_groups = {}
    singles = []
    for item in items:
        if item["meal_group_id"]:
            combo_groups.setdefault(item["meal_group_id"], []).append(item)
        else:
            singles.append(item)

    grouped_entries = []
    for group_items in combo_groups.values():
        if len(group_items) > 1:
            grouped_entries.append(("combo", group_items))
        else:
            grouped_entries.append(("single", group_items[0]))
    grouped_entries.extend(("single", item) for item in singles)
    return grouped_entries


def _render_day(day, items):
    category_count = len({item["category"] for item in items})
    recipe_count = len(items)
    st.markdown(
        dedent(
            f"""
        <div class="history-day-header">
            <div>
                <div class="history-day">{html.escape(str(day))}</div>
                <div class="history-day-sub">{t("history.day_summary", entries=recipe_count, categories=category_count)}</div>
            </div>
        </div>
        """,
        ).strip(),
        unsafe_allow_html=True,
    )

    for kind, payload in _split_grouped_items(items):
        if kind == "combo":
            group_id = payload[0]["meal_group_id"] if payload else "combo"
            _render_combo_card(payload, suffix=f"timeline_{day}_{group_id}")
        else:
            _render_entry_card(payload)
            _render_entry_actions(payload, suffix="timeline")


def _render_timeline(entries):
    grouped = _group_by_day(entries)
    day_options = list(grouped.keys())
    all_days = t("history.all_days")
    selected_day = st.selectbox(t("history.day_details"), [all_days] + day_options)
    days_to_render = day_options if selected_day == all_days else [selected_day]

    for cooked_day in days_to_render:
        with st.container(border=True):
            _render_day(cooked_day, grouped[cooked_day])


def _render_list(entries):
    for item in entries:
        with st.container(border=True):
            st.markdown(f"**{item['cooked_date']} - {html.escape(str(item['recipe_name']))}**")
            st.markdown(
                f"{_category_badge(item['category'])} {html.escape(_entry_details(item))}",
                unsafe_allow_html=True,
            )
            _render_entry_actions(item, suffix="list")


def render_history_page():
    st.subheader(t("history.title"))
    _render_manual_add()

    col1, col2, col3 = st.columns([1, 1, 1.4])
    start_date = col1.date_input(t("history.start_date"), value=date.today() - timedelta(days=30))
    end_date = col2.date_input(t("history.end_date"), value=date.today())
    query = col3.text_input(t("history.search"))

    entries = list_history(start_date=start_date, end_date=end_date, query=query)
    if not entries:
        st.info(t("history.empty"))
        return

    unique_recipes = len({item["recipe_id"] for item in entries})
    unique_days = len({item["cooked_date"] for item in entries})
    combo_count = len({item["meal_group_id"] for item in entries if item["meal_group_id"]})
    col_a, col_b, col_c = st.columns(3)
    col_a.metric(t("history.entries"), len(entries))
    col_b.metric(t("history.unique_recipes"), unique_recipes)
    col_c.metric(t("history.cooking_days"), unique_days)

    timeline_tab, list_tab = st.tabs([t("history.timeline"), t("history.list")])
    with timeline_tab:
        if combo_count:
            st.caption(t("history.combo_count", count=combo_count))
        _render_timeline(entries)

    with list_tab:
        _render_list(entries)
