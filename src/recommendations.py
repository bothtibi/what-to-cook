from src.history import recent_cooked_dates_by_recipe
from src.recommendation_algorithm import recipe_matches_max_prep_time, score_recipe
from src.recipes import list_recipes


def recommend_recipes(category="", limit=5, max_prep_time=90):
    recipes = list_recipes(category=category, include_disliked=False)
    recent_data = recent_cooked_dates_by_recipe()

    scored = []
    for recipe in recipes:
        if not recipe_matches_max_prep_time(recipe, max_prep_time):
            continue
        result = score_recipe(recipe, recent_data)
        if result is not None:
            scored.append((result["score"], recipe, result["reasons"]))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {"recipe": recipe, "score": score, "reasons": reasons}
        for score, recipe, reasons in scored[:limit]
    ]


def recommend_meal_combinations(limit=3, max_prep_time=90):
    soups = recommend_recipes(category="Leves", limit=max(limit * 2, 4), max_prep_time=max_prep_time)
    mains = recommend_recipes(category="Főétel", limit=max(limit * 2, 4), max_prep_time=max_prep_time)

    if not soups or not mains:
        return []

    combos = []
    for soup in soups:
        for main in mains:
            combo_score = (soup["score"] + main["score"]) / 2
            combos.append(
                {
                    "soup": soup,
                    "main": main,
                    "score": combo_score,
                    "reasons": [
                        *soup["reasons"][:1],
                        *main["reasons"][:1],
                    ],
                }
            )

    combos.sort(key=lambda item: item["score"], reverse=True)
    unique = []
    seen = set()
    for combo in combos:
        key = (combo["soup"]["recipe"]["id"], combo["main"]["recipe"]["id"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(combo)
        if len(unique) >= limit:
            break
    return unique
