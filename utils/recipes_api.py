import os, requests

BASE = "https://api.spoonacular.com"
SEARCH = f"{BASE}/recipes/complexSearch"
INFO = f"{BASE}/recipes/{{id}}/information"

def get_api_key():
    try:
        import streamlit as st
        k = st.secrets.get("SPOONACULAR_API_KEY")
    except Exception:
        k = None
    return k or os.environ.get("SPOONACULAR_API_KEY")

def _request(url, params):
    key = get_api_key()
    if not key:
        raise RuntimeError("Missing Spoonacular API key. Set SPOONACULAR_API_KEY.")
    p = dict(params or {})
    p["apiKey"] = key
    r = requests.get(url, params=p, timeout=30)
    if r.status_code == 402:
        raise RuntimeError("Spoonacular quota reached (HTTP 402). Reduce requests or upgrade plan.")
    r.raise_for_status()
    return r.json()

def complex_search(query="", number=10, offset=0, max_ingredients=None, max_ready_time=None, diet=None, intolerances=None, add_nutrition=True):
    params = {
        "query": query or "dinner",
        "number": number,
        "offset": offset,
        "instructionsRequired": True,
        "sort": "popularity",
    }
    if add_nutrition:
        params["addRecipeNutrition"] = True
    if max_ingredients:
        params["maxIngredientCount"] = max_ingredients
    if max_ready_time:
        params["maxReadyTime"] = max_ready_time
    if diet:
        params["diet"] = diet
    if intolerances:
        params["intolerances"] = intolerances
    return _request(SEARCH, params).get("results", [])

def recipe_information(recipe_id, includeNutrition=True):
    url = INFO.format(id=recipe_id)
    params = {"includeNutrition": "true" if includeNutrition else "false"}
    return _request(url, params)

def broad_fetch(themes, per_theme=20, pages=1, **filters):
    seen = set()
    results = []
    for theme in themes:
        for page in range(pages):
            offset = page * per_theme
            basic = complex_search(query=theme, number=per_theme, offset=offset, **filters)
            for r in basic:
                rid = r.get("id")
                if not rid or rid in seen: 
                    continue
                seen.add(rid)
                try:
                    info = recipe_information(rid, includeNutrition=True)
                except Exception:
                    info = r
                results.append(info)
    return results
