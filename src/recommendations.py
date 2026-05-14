import random
from datetime import date

from src.history import recent_cooked_dates_by_recipe
from src.recipes import list_recipes


def score_recipe(recipe, recent_data):
    if recipe["dislike_tibi"] and recipe["dislike_melinda"]:
        return None

    score = 10.0
    reasons = []
    data = recent_data.get(recipe["id"])

    favorite_points = int(bool(recipe["favorite_tibi"])) + int(bool(recipe["favorite_melinda"]))
    if favorite_points:
        score += favorite_points * 1.5
        reasons.append("kedvenc jeloles")

    if recipe["dislike_tibi"] or recipe["dislike_melinda"]:
        score -= 2.5
        reasons.append("valaki nem szereti")

    last_date = None
    if data:
        try:
            last_date = date.fromisoformat(data["last_cooked_date"])
        except (TypeError, ValueError):
            reasons.append("ervenytelen history datum kihagyva")

    if data and last_date:
        days_since = (date.today() - last_date).days
        stale_boost = min(days_since / 3.0, 10.0)
        frequency_penalty = min(data["cooked_count"] * 0.7, 5.0)
        score += stale_boost
        score -= frequency_penalty
        if days_since >= 10:
            reasons.append(f"regen fozve ({days_since} napja)")
        if data["cooked_count"] >= 3:
            reasons.append("gyakran keszult, kicsit visszafogva")
    elif not data:
        score += 4.0
        reasons.append("meg nem volt historyban")

    random_factor = random.uniform(-0.8, 0.8)
    score += random_factor
    if abs(random_factor) > 0.5:
        reasons.append("kis random faktor")
    return {"score": score, "reasons": reasons}


def recommend_recipes(category="", limit=5):
    recipes = list_recipes(category=category, include_disliked=False)
    recent_data = recent_cooked_dates_by_recipe()

    scored = []
    for recipe in recipes:
        result = score_recipe(recipe, recent_data)
        if result is not None:
            scored.append((result["score"], recipe, result["reasons"]))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        {"recipe": recipe, "score": score, "reasons": reasons}
        for score, recipe, reasons in scored[:limit]
    ]


def recommend_meal_combinations(limit=3):
    soups = recommend_recipes(category="Leves", limit=max(limit * 2, 4))
    mains = recommend_recipes(category="Főétel", limit=max(limit * 2, 4))

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
                        "egyensúly: leves + főétel",
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
