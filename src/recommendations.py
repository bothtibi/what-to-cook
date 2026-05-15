import random
from datetime import date

from src.history import recent_cooked_dates_by_recipe
from src.recipes import list_recipes


TAG_BOOSTS = {
    "gyors": 1.1,
    "kedvenc": 1.0,
    "klasszikus": 0.7,
    "sütőben": 0.4,
    "kiadós": 0.4,
}


def _recipe_tags(recipe):
    return {tag.strip().lower() for tag in str(recipe.get("tags", "")).split(",") if tag.strip()}


def score_recipe(recipe, recent_data):
    if recipe.get("is_archived") or recipe["dislike_tibi"] and recipe["dislike_melinda"]:
        return None

    score = 10.0
    reasons = []
    data = recent_data.get(recipe["id"])

    favorite_points = int(bool(recipe["favorite_tibi"])) + int(bool(recipe["favorite_melinda"]))
    if favorite_points:
        score += favorite_points * 2.0
        reasons.append("kedvenc")

    if recipe["dislike_tibi"] or recipe["dislike_melinda"]:
        score -= 4.0
        reasons.append("valaki nem szereti")

    tags = _recipe_tags(recipe)
    tag_score = sum(TAG_BOOSTS.get(tag, 0) for tag in tags)
    if tag_score:
        score += tag_score
        reasons.append("tagek alapjan jo valasztas")

    prep_time = int(recipe.get("prep_time_minutes", 0) or 0)
    if prep_time and prep_time <= 30:
        score += 0.8
        reasons.append("gyors")
    elif prep_time >= 90:
        score -= 0.8

    last_date = None
    if data:
        try:
            last_date = date.fromisoformat(data["last_cooked_date"])
        except (TypeError, ValueError):
            reasons.append("ervenytelen history datum kihagyva")

    if data and last_date:
        days_since = (date.today() - last_date).days
        if days_since < 3:
            score -= 8.0
            reasons.append("nagyon frissen volt")
        elif days_since < 7:
            score -= 3.5
            reasons.append("nemreg volt")

        stale_boost = min(days_since / 4.0, 8.0)
        frequency_penalty = min(data["cooked_count"] * 0.9, 6.0)
        score += stale_boost
        score -= frequency_penalty
        if days_since >= 14:
            reasons.append(f"regen fozve ({days_since} napja)")
        if data["cooked_count"] >= 3:
            reasons.append("gyakran keszult, kicsit visszafogva")
    elif not data:
        score += 3.0
        reasons.append("uj vagy regen nem hasznalt")

    random_factor = random.uniform(-0.35, 0.35)
    score += random_factor
    return {"score": score, "reasons": reasons}


def _matches_max_prep_time(recipe, max_prep_time):
    if not max_prep_time:
        return True
    prep_time = int(recipe.get("prep_time_minutes", 0) or 0)
    return prep_time == 0 or prep_time <= int(max_prep_time)


def recommend_recipes(category="", limit=5, max_prep_time=90):
    recipes = list_recipes(category=category, include_disliked=False)
    recent_data = recent_cooked_dates_by_recipe()

    scored = []
    for recipe in recipes:
        if not _matches_max_prep_time(recipe, max_prep_time):
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
