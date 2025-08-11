
import streamlit as st, pandas as pd, json, os
from utils.nutrition import rough_estimate_from_text
from utils.mfp import make_mfp_csv
from utils.heb import heb_prefill_text
from utils.stores import split_by_store

DATA_PATH = "data/app_state.json"
RECIPES_CSV = "data/recipes.csv"

st.set_page_config(page_title="Family Meal Planner", layout="wide")

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

st.title("🍽️ Family Meal Planner — MVP")

tabs = st.tabs(["Weekly Planner","Recipe Library","On‑Hand Builder","Shopping & Exports","Settings"])

with tabs[0]:
    st.subheader("Weekly Toggles")
    prof = state["profiles"]["default"]
    c1,c2,c3 = st.columns(3)
    with c1: prof["ingredient_limit"] = st.slider("Max ingredients per meal",3,20,prof.get("ingredient_limit",7))
    with c2: prof["max_prep_minutes"] = st.slider("Max prep time (minutes)",5,90,prof.get("max_prep_minutes",30),step=5)
    with c3: prof["batch_pref"] = st.selectbox("Batch‑prep preference",["Low","Medium","High"],index=["Low","Medium","High"].index(prof.get("batch_pref","Medium")))
    state["profiles"]["default"]=prof; save_state(state)

    st.markdown("### Auto‑generate weekly dinner plan (Spoonacular)")
    st.caption("Add key in Settings → Secrets: SPOONACULAR_API_KEY = \"your-key\"")
    diet = st.selectbox("Diet (optional)", ["","ketogenic","vegetarian","vegan","paleo","gluten free"], index=0)
    intolerances = st.text_input("Intolerances (optional, comma-separated)", placeholder="gluten, dairy, peanut")
    meals_per_week = st.slider("How many dinners this week?", 3, 7, 5)
    dinner_fraction = st.slider("Dinner share of daily calories", 0.2, 0.6, 0.35, step=0.05)
    if st.button("Generate Dinner Plan"):
        try:
            from utils.recipes_api import search_recipes
            from utils.macro import per_dinner_targets, score_recipe_to_targets
            res = search_recipes(
                number=meals_per_week*3,
                max_ingredients=prof.get("ingredient_limit",7),
                max_ready_time=prof.get("max_prep_minutes",30),
                diet=diet or None,
                intolerances=intolerances or None,
            )
            if not res: st.warning("No recipes returned. Try loosening filters.")
            else:
                targets = per_dinner_targets(prof, dinner_fraction)
                scored = []
                for r in res:
                    title = r.get("title","Untitled")
                    servings = r.get("servings",4)
                    ing_list=[]  # Spoonacular includes nutrition; ingredients may require a detail call. Placeholder list.
                    ingredients = "; ".join(ing_list) if ing_list else "See source"
                    cal=p=c=f_=0.0
                    for n in r.get("nutrition",{}).get("nutrients",[]):
                        nm=n.get("name","").lower()
                        if nm=="calories": cal=n.get("amount",0.0)
                        elif nm=="protein": p=n.get("amount",0.0)
                        elif nm=="carbohydrates": c=n.get("amount",0.0)
                        elif nm=="fat": f_=n.get("amount",0.0)
                    tmp={"title":title,"servings":servings,"est_cal":cal,"est_protein":p,"est_carbs":c,"est_fat":f_}
                    score = score_recipe_to_targets(tmp, targets)
                    scored.append((score,title,servings,ingredients,"See Spoonacular source",cal,p,c,f_))
                scored.sort(key=lambda x:x[0])
                pick = scored[:meals_per_week]
                added=0
                for (_s,title,servings,ingredients,steps,cal,p,c,f_) in pick:
                    if title not in recipes_df['title'].values:
                        recipes_df.loc[len(recipes_df)] = {
                            "title": title,"ingredients": ingredients,"steps": steps,"servings": servings,
                            "store_tag":"HEB","photo":"","favorite":False,"rating":0,
                            "est_cal":cal,"est_protein":p,"est_carbs":c,"est_fat":f_
                        }
                        added+=1
                save_recipes_df(recipes_df)
                st.success(f"Added {added} dinner(s) optimized for your macros. See 'Shopping & Exports'.")
        except Exception as e:
            st.error(f"Error: {e}")

with tabs[1]:
    st.subheader("Recipe Library")
    st.dataframe(recipes_df[["title","servings","store_tag","favorite","rating","est_cal","est_protein","est_carbs","est_fat"]], use_container_width=True)

with tabs[2]:
    st.subheader("On‑Hand Builder")
    have = st.text_area("Type items you have (comma‑separated)", "chicken breast, broccoli, greek yogurt, brown rice")
    if st.button("Suggest quick meal"):
        suggestion = {"title":"One‑Pan Protein & Veg","ingredients":have,"steps":"Sear protein; roast/steam veg; quick yogurt/lemon sauce.",
                      "servings":4,"store_tag":"HEB","photo":"","favorite":False,"rating":0,
                      "est_cal":350,"est_protein":30,"est_carbs":28,"est_fat":12}
        recipes_df.loc[len(recipes_df)] = suggestion
        save_recipes_df(recipes_df); st.success("Added suggested meal to library.")

with tabs[3]:
    st.subheader("Shopping & Exports")
    selected = st.multiselect("Choose recipes for this week", recipes_df["title"].tolist())
    if selected:
        sel = recipes_df[recipes_df["title"].isin(selected)]
        items=[]
        for _,r in sel.iterrows():
            parts=[x.strip() for x in str(r["ingredients"]).replace("\\n",";").split(";") if x.strip()]
            for p in parts: items.append({"item":p,"store":r.get("store_tag","HEB")})
        items_df = pd.DataFrame(items)
        buckets = split_by_store(items_df)
        st.markdown("**H‑E‑B pre‑fill list (copy/paste):**")
        import_text = heb_prefill_text(buckets.get("HEB", items_df))
        st.code(import_text)

        st.markdown("**Export to MyFitnessPal (CSV)**")
        path = "data/mfp_export.csv"
        if st.button("Create CSV for MFP"):
            make_mfp_csv(sel, path)
            with open(path,"rb") as f:
                st.download_button("Download mfp_export.csv", f, file_name="mfp_export.csv")
    else:
        st.info("Select recipes above to generate lists and exports.")

with tabs[4]:
    st.subheader("Settings")
    c1,c2,c3,c4 = st.columns(4)
    prof = state["profiles"]["default"]
    with c1: prof["calories"] = st.number_input("Calories/day",1200,4000,prof["calories"])
    with c2: prof["protein_g"] = st.number_input("Protein g/day",40,300,prof["protein_g"])
    with c3: prof["carbs_g"] = st.number_input("Carbs g/day",40,500,prof["carbs_g"])
    with c4: prof["fat_g"] = st.number_input("Fat g/day",20,200,prof["fat_g"])
    state["profiles"]["default"]=prof; save_state(state)
