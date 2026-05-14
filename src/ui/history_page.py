import html
from textwrap import dedent
from datetime import date, timedelta

import streamlit as st

from src.history import list_history


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
    return f'<span class="category-pill {_category_class(category)}">{html.escape(str(category))}</span>'


def _combo_badge():
    return '<span class="combo-pill">Kombináció</span>'


def _entry_details(item):
    details = [f"{int(item['days_planned'])} napra"]
    if item["quantity_note"]:
        details.append(f"mennyiség: {item['quantity_note']}")
    if item["notes"]:
        details.append(f"megjegyzés: {item['notes']}")
    if item["meal_group_id"]:
        details.append("kombináció része")
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


def _render_combo_card(items):
    recipe_names = " + ".join(html.escape(str(item["recipe_name"])) for item in items)
    badges = " ".join(_category_badge(item["category"]) for item in items)
    day_parts = [
        f"{item['recipe_name']}: {int(item['days_planned'])} napra"
        for item in items
    ]
    notes = [str(item["notes"]).strip() for item in items if item["notes"]]
    note_text = f" · megjegyzés: {html.escape(' | '.join(notes))}" if notes else ""

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
                <div class="history-day-sub">{recipe_count} bejegyzés · {category_count} kategória</div>
            </div>
        </div>
        """,
        ).strip(),
        unsafe_allow_html=True,
    )

    for kind, payload in _split_grouped_items(items):
        if kind == "combo":
            _render_combo_card(payload)
        else:
            _render_entry_card(payload)


def _render_timeline(entries):
    grouped = _group_by_day(entries)
    day_options = list(grouped.keys())
    selected_day = st.selectbox("Nap részletei", ["Összes nap"] + day_options)
    days_to_render = day_options if selected_day == "Összes nap" else [selected_day]

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


def render_history_page():
    st.subheader("Előzmények")
    col1, col2, col3 = st.columns([1, 1, 1.4])
    start_date = col1.date_input("Kezdő dátum", value=date.today() - timedelta(days=30))
    end_date = col2.date_input("Vég dátum", value=date.today())
    query = col3.text_input("Receptnév keresése")

    entries = list_history(start_date=start_date, end_date=end_date, query=query)
    if not entries:
        st.info("Nincs bejegyzés a megadott feltételekkel.")
        return

    unique_recipes = len({item["recipe_id"] for item in entries})
    unique_days = len({item["cooked_date"] for item in entries})
    combo_count = len({item["meal_group_id"] for item in entries if item["meal_group_id"]})
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Bejegyzések", len(entries))
    col_b.metric("Különböző receptek", unique_recipes)
    col_c.metric("Főzős napok", unique_days)

    timeline_tab, list_tab = st.tabs(["Interaktív idővonal", "Lista"])
    with timeline_tab:
        if combo_count:
            st.caption(f"{combo_count} leves + főétel kombináció található a szűrésben.")
        _render_timeline(entries)

    with list_tab:
        _render_list(entries)
