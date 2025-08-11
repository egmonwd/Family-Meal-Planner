import os, requests
ANALYZE_URL = "https://api.spoonacular.com/recipes/parseIngredients"
def _get_key():
    try:
        import streamlit as st
        k = st.secrets.get("SPOONACULAR_API_KEY")
    except Exception:
        k=None
    return k or os.environ.get("SPOONACULAR_API_KEY")
def analyze_ingredients(ingredients_text, servings=1):
    key=_get_key()
    if not key: raise RuntimeError("Missing SPOONACULAR_API_KEY for nutrition analysis.")
    lines=[ln.strip() for ln in ingredients_text.replace(";","\n").splitlines() if ln.strip()]
    total={"calories":0.0,"protein_g":0.0,"carbs_g":0.0,"fat_g":0.0}
    for ln in lines:
        r=requests.get(ANALYZE_URL, params={"apiKey":key,"ingredientList":ln,"servings":servings}, timeout=30)
        if r.status_code==402: raise RuntimeError("Spoonacular quota reached during nutrition analysis (402).")
        r.raise_for_status()
        js=r.json() if isinstance(r.json(),list) else [r.json()]
        for e in js:
            nutr=e.get("nutrition",{}).get("nutrients",[])
            cal=p=c=f=0.0
            for n in nutr:
                nm=n.get("name","").lower()
                if nm=="calories": cal=n.get("amount",0.0)
                elif nm=="protein": p=n.get("amount",0.0)
                elif nm=="carbohydrates": c=n.get("amount",0.0)
                elif nm=="fat": f=n.get("amount",0.0)
            total["calories"]+=cal; total["protein_g"]+=p; total["carbs_g"]+=c; total["fat_g"]+=f
    for k in total: total[k]=total[k]/max(servings,1)
    return total
