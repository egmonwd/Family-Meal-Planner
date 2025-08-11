
import streamlit as st, pandas as pd, json, os
from utils.mfp import make_mfp_csv
from utils.heb import heb_prefill_text
from utils.stores import split_by_store

DATA_PATH = "data/app_state.json"
RECIPES_CSV = "data/recipes.csv"

st.set_page_config(page_title="Family Meal Planner — Milestone B", layout="wide")

def load_state():
    with open(DATA_PATH,"r") as f: return json.load(f)
def save_state(state):
    with open(DATA_PATH,"w") as f: json.dump(state,f,indent=2)
def load_recipes_df():
    if os.path.exists(RECIPES_CSV): return pd.read_csv(RECIPES_CSV)
    return pd.DataFrame(columns=["title","ingredients","steps","servings","store_tag","photo","favorite","rating","est_cal","est_protein","est_carbs","est_fat"])
def save_recipes_df(df): df.to_csv(RECIPES_CSV,index=False)

state = load_state()
recipes_df = load_recipes_df()

st.title("🍽️ Family Meal Planner — Milestone B")

tabs = st.tabs(["Profiles","Weekly Planner","Full‑Week Generator","Recipe Library","Shopping & Exports","Batch‑Prep Guide"])

# Profiles
with tabs[0]:
    st.subheader("Family Profiles")
    profs = state["profiles"]
    cols = st.columns(len(profs))
    keys = list(profs.keys())
    for i,k in enumerate(keys):
        with cols[i]:
            st.markdown(f"**{k.title()}**")
            p = profs[k]
            p["calories"]   = st.number_input(f"{k} cals/day", 800, 5000, p.get("calories",2000))
            p["protein_g"]  = st.number_input(f"{k} protein g", 20, 300, p.get("protein_g",120))
            p["carbs_g"]    = st.number_input(f"{k} carbs g", 20, 500, p.get("carbs_g",180))
            p["fat_g"]      = st.number_input(f"{k} fat g", 20, 200, p.get("fat_g",70))
            profs[k]=p
    state["profiles"]=profs; save_state(state)
    st.success("Saved profiles.")

# Weekly Planner
with tabs[1]:
    st.subheader("Headcount, constraints & store preferences")
    settings = state["settings"]
    st.markdown("**Dinner headcount:**")
    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    for d in days:
        st.markdown(f"**{d}**")
        cols = st.columns(len(state["profiles"]))
        for i,k in enumerate(state["profiles"].keys()):
            settings["headcount"][d][k] = cols[i].toggle(k, value=settings["headcount"][d].get(k, False), key=f"{d}_{k}")
    st.divider()
    c1,c2,c3 = st.columns(3)
    with c1: settings["ingredient_limit"] = st.slider("Max ingredients/meal",3,20,settings.get("ingredient_limit",7))
    with c2: settings["max_prep_minutes"] = st.slider("Max prep time (min)",5,90,settings.get("max_prep_minutes",30),step=5)
    with c3: settings["batch_pref"] = st.selectbox("Batch‑prep preference",["Low","Medium","High"], index=["Low","Medium","High"].index(settings.get("batch_pref","Medium")))
    st.divider()
    st.markdown("**Macro split by meal type (must total 1.00):**")
    ms = settings["macro_split"]
    c1,c2,c3,c4 = st.columns(4)
    with c1: ms["Breakfast"] = st.number_input("Breakfast fraction", 0.00, 0.80, ms.get("Breakfast",0.25), step=0.05)
    with c2: ms["Lunch"]     = st.number_input("Lunch fraction", 0.00, 0.80, ms.get("Lunch",0.35), step=0.05)
    with c3: ms["Snack"]     = st.number_input("Snack fraction", 0.00, 0.80, ms.get("Snack",0.10), step=0.05)
    with c4: ms["Dinner"]    = st.number_input("Dinner fraction", 0.00, 0.80, ms.get("Dinner",0.30), step=0.05)
    settings["macro_split"]=ms
    st.markdown("**Store preferences (category → preferred store):**")
    sp = settings["store_preferences"]
    c1,c2,c3 = st.columns(3)
    with c1: sp["produce"] = st.selectbox("Produce", ["HEB","Costco","Aldi"], index=["HEB","Costco","Aldi"].index(sp.get("produce","Aldi")))
    with c2: sp["meat"]    = st.selectbox("Meat", ["HEB","Costco","Aldi"], index=["HEB","Costco","Aldi"].index(sp.get("meat","HEB")))
    with c3: sp["pantry"]  = st.selectbox("Pantry", ["HEB","Costco","Aldi"], index=["HEB","Costco","Aldi"].index(sp.get("pantry","Costco")))
    settings["store_preferences"]=sp
    state["settings"]=settings; save_state(state)

# Full‑Week Generator
with tabs[2]:
    st.subheader("Generate Breakfast • Lunch • Snack • Dinner")
    st.caption("Spoonacular key in Secrets as SPOONACULAR_API_KEY. Free tier has quota; use 'Library-only' to avoid API calls.")
    diet = st.selectbox("Diet (optional)", ["","ketogenic","vegetarian","vegan","paleo","gluten free"], index=0)
    intolerances = st.text_input("Intolerances (optional)", "")
    breadth = st.select_slider("Search breadth", options=["Narrow","Balanced","Wide"], value="Balanced")
    if breadth == "Narrow": themes, per_theme, pages = ["dinner"], 20, 1
    elif breadth == "Wide": themes, per_theme, pages = ["dinner","bowl","skillet","sheet pan","stir fry","tacos","salad","wrap"], 20, 2
    else: themes, per_theme, pages = ["dinner","bowl","skillet","salad"], 20, 1

    meals_per_day = state["settings"]["meals_per_day"]
    c1,c2,c3,c4 = st.columns(4)
    with c1: meals_per_day["Breakfast"] = st.number_input("Breakfasts/day", 0, 2, meals_per_day.get("Breakfast",1))
    with c2: meals_per_day["Lunch"]     = st.number_input("Lunches/day", 0, 2, meals_per_day.get("Lunch",1))
    with c3: meals_per_day["Snack"]     = st.number_input("Snacks/day", 0, 2, meals_per_day.get("Snack",1))
    with c4: meals_per_day["Dinner"]    = st.number_input("Dinners/day", 0, 2, meals_per_day.get("Dinner",1))
    state["settings"]["meals_per_day"]=meals_per_day; save_state(state)

    st.caption("Quota guard & fallback")
    api_cap = st.slider("Max API calls this run", 5, 80, 30, step=5)
    lib_only = st.toggle("Library-only fallback (no API calls)", value=False)

    if st.button("Generate Full Week"):
        try:
            from utils.recipes_api import broad_fetch
            from utils.macro import per_meal_targets, score_recipe_to_targets
            fetched = [] if lib_only else broad_fetch(
                themes=themes, per_theme=per_theme, pages=pages,
                max_ingredients=state["settings"]["ingredient_limit"],
                max_ready_time=state["settings"]["max_prep_minutes"],
                diet=diet or None, intolerances=intolerances or None,
            )
            if api_cap <= 20:
                pages = 1
            elif api_cap <= 40:
                pages = min(pages,1)

            if lib_only:
                st.info("Using your Recipe Library only (no API calls).")
                fetched = []
                for _, r in recipes_df.iterrows():
                    fetched.append({
                        "title": r["title"],
                        "servings": int(r.get("servings",4)),
                        "nutrition": {"nutrients": [
                            {"name":"Calories","amount": float(r.get("est_cal",0))},
                            {"name":"Protein","amount": float(r.get("est_protein",0))},
                            {"name":"Carbohydrates","amount": float(r.get("est_carbs",0))},
                            {"name":"Fat","amount": float(r.get("est_fat",0))},
                        ]},
                        # Allow basic ingredient text passthrough
                        "extendedIngredients": [{"original": it.strip()} for it in str(r.get("ingredients","")).split(";") if it.strip()]
                    })

            if not fetched:
                st.warning("No recipes returned. Loosen filters, widen search, or enable Library-only.")
            else:
                you = state["profiles"]["you"]
                ms = state["settings"]["macro_split"]
                plan = {"Breakfast":[], "Lunch":[], "Snack":[], "Dinner":[]}
                for meal_type in ["Breakfast","Lunch","Snack","Dinner"]:
                    fraction = ms.get(meal_type, 0.25)
                    targets = per_meal_targets(you, fraction)
                    scored=[]
                    for r in fetched:
                        title = r.get("title","Untitled")
                        servings = r.get("servings",4)
                        nutr = (r.get("nutrition") or {}).get("nutrients", [])
                        cal=p=c=f_=0.0
                        for n in nutr:
                            nm=n.get("name","").lower()
                            if nm=="calories": cal=n.get("amount",0.0)
                            elif nm=="protein": p=n.get("amount",0.0)
                            elif nm=="carbohydrates": c=n.get("amount",0.0)
                            elif nm=="fat": f_=n.get("amount",0.0)
                        tmp={"title":title,"servings":servings,"est_cal":cal,"est_protein":p,"est_carbs":c,"est_fat":f_}
                        score=score_recipe_to_targets(tmp, targets)
                        scored.append((score,title,servings,cal,p,c,f_, r.get("extendedIngredients",[])))
                    scored.sort(key=lambda x:x[0])
                    need = 7 * max(0, int(meals_per_day.get(meal_type,1)))
                    pick = scored[:need]
                    plan[meal_type] = pick

                added=0
                for meal_type, items in plan.items():
                    for (_s,title,servings,cal,p,c,f_, ex_ings) in items:
                        # Build cleaner ingredient text
                        ing_texts = []
                        for ing in ex_ings:
                            # Prefer Spoonacular's "original" field for human-readable strings
                            orig = ing.get("original") if isinstance(ing, dict) else None
                            if orig: ing_texts.append(orig)
                            else:
                                name = (ing.get("name") or ing.get("originalName") or "").strip() if isinstance(ing, dict) else ""
                                amt = ing.get("amount", "") if isinstance(ing, dict) else ""
                                unit = ing.get("unit", "") if isinstance(ing, dict) else ""
                                if name:
                                    ing_texts.append(f"{name} {amt} {unit}".strip())
                        ingredients = "; ".join([t for t in ing_texts if t])
                        if title not in recipes_df['title'].values:
                            recipes_df.loc[len(recipes_df)] = {
                                "title": title, "ingredients": ingredients if ingredients else "See source",
                                "steps": "See Spoonacular",
                                "servings": servings, "store_tag": "HEB",
                                "photo": "", "favorite": False, "rating": 0,
                                "est_cal": cal, "est_protein": p, "est_carbs": c, "est_fat": f_,
                            }
                            added+=1
                save_recipes_df(recipes_df)
                st.success(f"Generated full-week plan and added {added} new items to library. See Batch‑Prep Guide & Shopping tabs.")
        except Exception as e:
            msg = str(e)
            if 'quota' in msg.lower() or '402' in msg:
                st.warning('Hit Spoonacular quota (HTTP 402). Try Library-only mode, Narrow breadth, or lower Max API calls.')
            else:
                st.error(f"Error: {e}")

# Recipe Library
with tabs[3]:
    st.subheader("Your Recipe Library")
    st.dataframe(recipes_df[["title","servings","store_tag","favorite","rating","est_cal","est_protein","est_carbs","est_fat"]], use_container_width=True)

# Shopping & Exports
with tabs[4]:
    st.subheader("Build Shopping List")
    selected = st.multiselect("Choose recipes for this week", recipes_df["title"].tolist())
    if selected:
        sel = recipes_df[recipes_df["title"].isin(selected)].copy()
        # Budget/store tweaks: route items by category → preferred store
        def classify(item: str):
            s=item.lower()
            if any(x in s for x in ["broccoli","spinach","onion","pepper","apple","banana","avocado"]): return "produce"
            if any(x in s for x in ["chicken","beef","salmon","pork","turkey"]): return "meat"
            return "pantry"
        prefs = state["settings"]["store_preferences"]
        items=[]
        for _,r in sel.iterrows():
            parts=[x.strip() for x in str(r["ingredients"]).replace("\\n",";").split(";") if x.strip()]
            for p in parts:
                cat = classify(p)
                store = prefs.get(cat, "HEB")
                items.append({"item":p,"store":store,"category":cat})
        items_df = pd.DataFrame(items) if items else pd.DataFrame([{"item":"(Open recipe link for ingredients)","store":"HEB","category":"pantry"}])
        buckets = split_by_store(items_df)
        st.markdown("**H‑E‑B pre‑fill list (copy/paste):**")
        heb_df = buckets.get("HEB", pd.DataFrame(columns=items_df.columns))
        from utils.heb import heb_prefill_text
        st.code(heb_prefill_text(heb_df if not heb_df.empty else pd.DataFrame([{"item":"(No parsed items)"}])))

        st.markdown("**Export to MyFitnessPal (CSV)**")
        path = "data/mfp_export.csv"
        if st.button("Create CSV for MFP"):
            make_mfp_csv(sel, path)
            with open(path,"rb") as f:
                st.download_button("Download mfp_export.csv", f, file_name="mfp_export.csv")
    else:
        st.info("Select recipes above to generate lists and exports.")

# Batch‑Prep Guide
with tabs[5]:
    st.subheader("Batch‑Prep Guide")
    chosen = st.multiselect("Select recipes to prep", recipes_df["title"].tolist())
    if chosen:
        subset = recipes_df[recipes_df["title"].isin(chosen)]
        from utils.prep import build_prep_tasks
        plan = build_prep_tasks(subset)
        for section, tasks in plan:
            st.markdown(f"### {section}")
            for name, minutes in tasks:
                if minutes > 0:
                    st.write(f"• {name} — ~{int(minutes)} min")
        st.caption("Time estimates are rough; tune rules in utils/prep.py as you learn your flow.")
    else:
        st.info("Pick some recipes to see combined prep tasks.")
