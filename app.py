import streamlit as st

from utils.recipe_service import find_recipes


st.set_page_config(page_title="What to Cook", layout="centered")

st.title("What to Cook")
st.write("Enter ingredients you have at home and get simple recipe ideas.")

ingredients_text = st.text_input(
    "Ingredients (comma-separated)",
    placeholder="egg, tomato, onion",
)
max_time = st.slider("Max cooking time (minutes)", min_value=5, max_value=60, value=30)
vegetarian_only = st.checkbox("Vegetarian only", value=False)

if st.button("Find recipes"):
    ingredients = [item.strip() for item in ingredients_text.split(",")]
    results = find_recipes(ingredients, max_time, vegetarian_only)

    if not results:
        st.warning("No matches found. Try adding more ingredients or increasing max time.")
    else:
        st.success(f"Found {len(results)} recipe(s).")
        for recipe in results:
            with st.container(border=True):
                st.subheader(recipe["name"])
                st.write(recipe["description"])
                st.write(f"Time: {recipe['max_time']} min")
                st.write(f"Ingredients: {', '.join(recipe['ingredients'])}")