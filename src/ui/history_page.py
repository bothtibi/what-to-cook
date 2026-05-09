from datetime import date, timedelta

import streamlit as st

from src.history import list_history


def _group_by_day(entries):
    grouped = {}
    for item in entries:
        grouped.setdefault(item["cooked_date"], []).append(item)
    return grouped


def render_history_page():
    st.subheader("Elozmenyek")
    col1, col2, col3, col4 = st.columns(4)
    start_date = col1.date_input("Kezdo datum", value=date.today() - timedelta(days=30))
    end_date = col2.date_input("Veg datum", value=date.today())
    query = col3.text_input("Receptnev keresese")
    view_mode = col4.selectbox("Nezet", ["idovonal", "lista"])

    entries = list_history(start_date=start_date, end_date=end_date, query=query)
    if not entries:
        st.info("Nincs bejegyzes a megadott feltetelekkel.")
        return

    unique_recipes = len({item["recipe_id"] for item in entries})
    col_a, col_b = st.columns(2)
    col_a.metric("Bejegyzesek", len(entries))
    col_b.metric("Kulonbozo receptek", unique_recipes)

    if view_mode == "idovonal":
        grouped = _group_by_day(entries)
        for cooked_day, items in grouped.items():
            with st.container(border=True):
                st.markdown(f"### {cooked_day}")
                for item in items:
                    st.markdown(f"- **{item['recipe_name']}** ({item['category']}, {item['days_planned']} nap)")
                    extras = []
                    if item["quantity_note"]:
                        extras.append(f"mennyiseg: {item['quantity_note']}")
                    if item["meal_group_id"]:
                        extras.append(f"group: {item['meal_group_id']}")
                    if item["notes"]:
                        extras.append(f"megjegyzes: {item['notes']}")
                    if extras:
                        st.caption(" | ".join(extras))
    else:
        for item in entries:
            with st.container(border=True):
                st.markdown(f"**{item['cooked_date']} - {item['recipe_name']}**")
                st.write(f"Kategoria: {item['category']} | Napok: {item['days_planned']}")
                if item["quantity_note"]:
                    st.write(f"Mennyiseg: {item['quantity_note']}")
                if item["meal_group_id"]:
                    st.write(f"Meal group: {item['meal_group_id']}")
                if item["notes"]:
                    st.write(f"Megjegyzes: {item['notes']}")
