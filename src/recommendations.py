import random
from datetime import date

from src.history import recent_cooked_dates_by_recipe
from src.recipes import list_recipes


def score_recipe(recipe, recent_data):
    if recipe["is_blocked"]:
        return None

    score = 10.0
    data = recent_data.get(recipe["id"])

    if recipe["is_favorite"]:
        score += 2.0

    if data:
        last_date = date.fromisoformat(data["last_cooked_date"])
        days_since = (date.today() - last_date).days
        score += min(days_since / 3.0, 10.0)
        score -= min(data["cooked_count"] * 0.7, 5.0)
    else:
        score += 4.0

    score += random.uniform(-0.8, 0.8)
    return score


def recommend_recipes(category="", limit=5):
    recipes = list_recipes(category=category, include_blocked=False)
    recent_data = recent_cooked_dates_by_recipe()

    scored = []
    for recipe in recipes:
        score = score_recipe(recipe, recent_data)
        if score is not None:
            scored.append((score, recipe))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [recipe for _, recipe in scored[:limit]]
