import json
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "recipes.json"


def load_recipes():
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def find_recipes(user_ingredients, max_time, vegetarian_only):
    recipes = load_recipes()
    user_set = {item.strip().lower() for item in user_ingredients if item.strip()}
    matches = []

    for recipe in recipes:
        if recipe["max_time"] > max_time:
            continue
        if vegetarian_only and not recipe["vegetarian"]:
            continue

        recipe_set = {item.lower() for item in recipe["ingredients"]}
        common_count = len(user_set & recipe_set)
        if common_count == 0:
            continue

        matches.append((common_count, recipe))

    matches.sort(key=lambda item: item[0], reverse=True)
    return [recipe for _, recipe in matches]
