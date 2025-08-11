
import streamlit as st, pandas as pd, json, os, uuid
from utils.mfp import make_mfp_csv
from utils.heb import heb_prefill_text
from utils.stores import split_by_store

DATA_PATH = "data/app_state.json"
RECIPES_CSV = "data/recipes.csv"
UPLOAD_DIR = "data/uploads"

st.set_page_config(page_title="Family Meal Planner — Milestone E+", layout="wide")

def load_state():
    with open(DATA_PATH,"r") as f: return json.load(f)
def save_state(state):
    with open(DATA_PATH,"w") as f: json.dump(state,f,indent=2)
def load_recipes_df():
    if os.path.exists(RECIPES_CSV): return pd.read_csv(RECIPES_CSV)
    return pd.DataFrame(columns=["title","ingredients","steps","servings","store_tag","photo","favorite","rating","est_cal","est_protein","est_carbs","est_fat","source_url"])
def save_recipes_df(df): df.to_csv(RECIPES_CSV,index=False)

state = load_state()
recipes_df = load_recipes_df()

st.title("🍽️ Family Meal Planner — Milestone E+")

tabs = st.tabs([
    "Profiles","Weekly Planner","Full‑Week Generator",
    "Recipe Library","Pantry","Shopping & Exports","Batch‑Prep Guide","Store Cadence & Prices"
])

# ---------- Profiles ----------
with tabs[0]:
    st.subheader("Family Profiles — daily calories & macros")
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

# ---------- Weekly Planner ----------
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

# ---------- Full‑Week Generator (favorites‑first, quota guard, breadth) ----------
with tabs[2]:
    st.subheader("Generate Breakfast • Lunch • Snack • Dinner (Favorites‑first)")
    st.caption("Requires Spoonacular key in Secrets as `SPOONACULAR_API_KEY`. Free tier has quota; use Library‑only to avoid API calls.")
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
    lib_only = st.toggle("Library‑only fallback (no API calls)", value=False)
    prioritize_faves = st.toggle("Prioritize favorites (5★ first)", value=True)

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
            if api_cap <= 20: pages = 1
            elif api_cap <= 40: pages = min(pages,1)

            lib_pool = recipes_df.copy()

            def pick_best(df_pool, targets, needed):
                scored=[]
                for _, r in df_pool.iterrows():
                    tmp={"title":r["title"],"servings":int(r.get("servings",4)),
                         "est_cal":float(r.get("est_cal",0)),"est_protein":float(r.get("est_protein",0)),
                         "est_carbs":float(r.get("est_carbs",0)),"est_fat":float(r.get("est_fat",0))}
                    s = score_recipe_to_targets(tmp, targets)
                    scored.append((s, r["title"]))
                scored.sort(key=lambda x:x[0])
                return [t for _, t in scored[:needed]]

            # Convert fetched API results to DF for scoring
            api_rows=[]
            for r in fetched:
                cal=p=c=f_=0.0
                for n in (r.get("nutrition") or {}).get("nutrients", []):
                    nm=n.get("name","").lower()
                    if nm=="calories": cal=n.get("amount",0.0)
                    elif nm=="protein": p=n.get("amount",0.0)
                    elif nm=="carbohydrates": c=n.get("amount",0.0)
                    elif nm=="fat": f_=n.get("amount",0.0)
                api_rows.append({
                    "title": r.get("title","Untitled"),
                    "servings": r.get("servings",4),
                    "est_cal": cal, "est_protein": p, "est_carbs": c, "est_fat": f_,
                    "ingredients": "; ".join([(ing.get("original") or "").strip() for ing in r.get("extendedIngredients",[]) if ing.get("original")])
                })
            api_df = pd.DataFrame(api_rows) if api_rows else pd.DataFrame(columns=["title","servings","est_cal","est_protein","est_carbs","est_fat","ingredients"])

            you = state["profiles"]["you"]
            ms = state["settings"]["macro_split"]
            plan = {"Breakfast":[], "Lunch":[], "Snack":[], "Dinner":[]}
            new_adds = []

            for meal_type in ["Breakfast","Lunch","Snack","Dinner"]:
                fraction = ms.get(meal_type, 0.25)
                targets = per_meal_targets(you, fraction)
                need = 7 * max(0, int(meals_per_day.get(meal_type,1)))

                chosen = []

                if prioritize_faves and not lib_pool.empty:
                    faves = lib_pool[(lib_pool["favorite"]==True) & (lib_pool["rating"]>=5)]
                    if not faves.empty:
                        chosen += pick_best(faves, targets, min(len(faves), need))

                if len(chosen) < need and not lib_pool.empty:
                    remaining = need - len(chosen)
                    non_faves = lib_pool[~lib_pool["title"].isin(chosen)]
                    if not non_faves.empty:
                        chosen += pick_best(non_faves, targets, remaining)

                if len(chosen) < need and not api_df.empty and not lib_only:
                    remaining = need - len(chosen)
                    api_best = api_df[~api_df["title"].isin(chosen)]
                    api_pick_titles = pick_best(api_best, targets, min(remaining, len(api_best)))
                    chosen += api_pick_titles
                    for t in api_pick_titles:
                        row = api_best[api_best["title"]==t].iloc[0]
                        if t not in recipes_df['title'].values:
                            new_adds.append({
                                "title": t, "ingredients": row.get("ingredients","See source"),
                                "steps": "See Spoonacular", "servings": int(row.get("servings",4)),
                                "store_tag":"HEB","photo":"","favorite":False,"rating":0,
                                "est_cal": float(row.get("est_cal",0)),"est_protein": float(row.get("est_protein",0)),
                                "est_carbs": float(row.get("est_carbs",0)),"est_fat": float(row.get("est_fat",0)),
                                "source_url": ""
                            })

                plan[meal_type] = chosen

            if new_adds:
                recipes_df = pd.concat([recipes_df, pd.DataFrame(new_adds)], ignore_index=True)
                save_recipes_df(recipes_df)

            st.success("Full week generated. Check Recipe Library → Shopping & Exports for lists and exports.")

        except Exception as e:
            msg = str(e)
            if 'quota' in msg.lower() or '402' in msg:
                st.warning('Hit Spoonacular quota (HTTP 402). Try Library‑only mode, Narrow breadth, or lower Max API calls.')
            else:
                st.error(f"Error: {e}")

# ---------- Recipe Library (link import, paste, file + auto nutrition) ----------
with tabs[3]:
    st.subheader("Recipe Library")
    st.dataframe(recipes_df[["title","servings","store_tag","favorite","rating","est_cal","est_protein","est_carbs","est_fat","source_url"]], use_container_width=True)

    st.markdown("### Add / Import")
    mode = st.radio("Add by", ["Link (auto‑scrape)","Paste text","Upload file (PDF/Image/TXT)"])
    title = st.text_input("Title (optional)")
    servings = st.number_input("Servings", 1, 20, 4)
    store_tag = st.selectbox("Default store", ["HEB","Costco","Aldi"])
    favorite = st.toggle("Mark as favorite", value=False)
    rating = st.slider("Rating", 0, 5, 0)

    ingredients = ""; steps=""; source_url=""; photo=""; cal=pro=carb=fat=0.0

    if mode == "Link (auto‑scrape)":
        url = st.text_input("Recipe URL")
        if st.button("Import from URL"):
            try:
                from utils.recipe_import import import_from_url
                rec = import_from_url(url)
                title = title or rec["title"]
                servings = rec["servings"]
                ingredients = rec["ingredients"]; steps = rec["steps"]; photo = rec["photo"]; source_url = rec["source_url"]
                cal = rec["est_cal"]; pro = rec["est_protein"]; carb = rec["est_carbs"]; fat = rec["est_fat"]
                if (cal==0 or pro==0 or carb==0 or fat==0) and ingredients:
                    try:
                        from utils.nutrition_api import analyze_ingredients
                        est = analyze_ingredients(ingredients, servings=servings)
                        cal,pro,carb,fat = est["calories"], est["protein_g"], est["carbs_g"], est["fat_g"]
                        st.info("Filled nutrition via Spoonacular analysis.")
                    except Exception as e:
                        st.warning(f"Nutrition analysis skipped: {e}")
                new = {"title": title or "Imported Recipe","ingredients": ingredients,"steps": steps,"servings": servings,
                       "store_tag": store_tag,"photo": photo,"favorite": favorite,"rating": rating,
                       "est_cal": cal,"est_protein": pro,"est_carbs": carb,"est_fat": fat,"source_url": source_url}
                recipes_df.loc[len(recipes_df)] = new; save_recipes_df(recipes_df)
                st.success(f"Imported “{new['title']}”.")
            except Exception as e:
                st.error(f"Import failed: {e}")

    elif mode == "Paste text":
        ingredients = st.text_area("Ingredients (one per line or ; separated)")
        steps = st.text_area("Steps")
        cal = st.number_input("Calories/serving", 0, 2000, 0)
        pro = st.number_input("Protein g/serving", 0, 200, 0)
        carb = st.number_input("Carbs g/serving", 0, 300, 0)
        fat = st.number_input("Fat g/serving", 0, 150, 0)
        auto = st.toggle("Auto‑fill nutrition", value=True)
        if st.button("Add to Library"):
            if auto and ingredients and (cal==0 or pro==0 or carb==0 or fat==0):
                try:
                    from utils.nutrition_api import analyze_ingredients
                    est = analyze_ingredients(ingredients, servings=servings)
                    cal,pro,carb,fat = est["calories"], est["protein_g"], est["carbs_g"], est["fat_g"]
                    st.info("Filled nutrition via Spoonacular analysis.")
                except Exception as e:
                    st.warning(f"Nutrition analysis skipped: {e}")
            new = {"title": title or "Untitled","ingredients": ingredients,"steps": steps,"servings": servings,
                   "store_tag": store_tag,"photo": "","favorite": favorite,"rating": rating,
                   "est_cal": cal,"est_protein": pro,"est_carbs": carb,"est_fat": fat,"source_url": ""}
            recipes_df.loc[len(recipes_df)] = new; save_recipes_df(recipes_df); st.success("Recipe added.")

    else:
        up = st.file_uploader("Upload PDF/Image/TXT", type=["pdf","png","jpg","jpeg","txt"])
        if up is not None:
            fname = f"{uuid.uuid4().hex}_{up.name}"; path = os.path.join(UPLOAD_DIR, fname)
            with open(path,"wb") as f: f.write(up.read())
            st.success(f"Saved file: {fname}")
            text = ""
            try:
                if fname.lower().endswith(".pdf"):
                    from utils.ocr import extract_pdf_text; text = extract_pdf_text(path)
                elif fname.lower().endswith(".txt"):
                    with open(path,"r",encoding="utf-8",errors="ignore") as rf: text = rf.read()
                else:
                    api_key = st.secrets.get("OCR_SPACE_API_KEY", None)
                    if api_key:
                        from utils.ocr import ocr_image_via_ocrspace
                        with open(path,"rb") as imgf: text = ocr_image_via_ocrspace(imgf.read(), api_key)
                    else:
                        st.info("No OCR key set; paste from image manually.")
            except Exception as e:
                st.warning(f"OCR/Text extraction error: {e}")
            st.text_area("Extracted text (edit)", value=text, height=200)
            ingredients = st.text_area("Ingredients", value="")
            steps = st.text_area("Steps", value="")
            cal = st.number_input("Calories/serving", 0, 2000, 0, key="file_cal")
            pro = st.number_input("Protein g/serving", 0, 200, 0, key="file_pro")
            carb = st.number_input("Carbs g/serving", 0, 300, 0, key="file_carb")
            fat = st.number_input("Fat g/serving", 0, 150, 0, key="file_fat")
            auto = st.toggle("Auto‑fill nutrition", value=True, key="file_auto")
            if st.button("Add to Library", key="file_add"):
                if auto and ingredients and (cal==0 or pro==0 or carb==0 or fat==0):
                    try:
                        from utils.nutrition_api import analyze_ingredients
                        est = analyze_ingredients(ingredients, servings=servings)
                        cal,pro,carb,fat = est["calories"], est["protein_g"], est["carbs_g"], est["fat_g"]
                        st.info("Filled nutrition via Spoonacular analysis.")
                    except Exception as e:
                        st.warning(f"Nutrition analysis skipped: {e}")
                new = {"title": title or up.name,"ingredients": ingredients,"steps": steps,"servings": servings,
                       "store_tag": store_tag,"photo": "","favorite": favorite,"rating": rating,
                       "est_cal": cal,"est_protein": pro,"est_carbs": carb,"est_fat": fat,"source_url": ""}
                recipes_df.loc[len(recipes_df)] = new; save_recipes_df(recipes_df); st.success("Recipe added.")

# ---------- Pantry ----------
with tabs[4]:
    st.subheader("Pantry — on‑hand items (quantity‑aware)")
    pantry = state.get("pantry", [])
    c1,c2,c3 = st.columns(3)
    with c1: p_item = st.text_input("Item (e.g., chicken breast 2 lb)")
    with c2: p_qty = st.number_input("Quantity", 0.0, 9999.0, 0.0, step=0.5)
    with c3: p_unit = st.text_input("Unit (lb, cup, can, etc.)", value="")
    if st.button("Add pantry item"):
        pantry.append({"item": p_item, "quantity": p_qty, "unit": p_unit})
        state["pantry"]=pantry; save_state(state); st.success("Added to pantry.")
    if pantry:
        st.table(pd.DataFrame(pantry))

# ---------- Shopping & Exports ----------
with tabs[5]:
    st.subheader("Build Shopping List (pantry‑aware + cost estimate)")
    selected = st.multiselect("Choose recipes for this week", recipes_df["title"].tolist())
    if selected:
        sel = recipes_df[recipes_df["title"].isin(selected)].copy()
        # Parse ingredients into line items; route by simple category → preferred store
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
                cat = classify(p); store = prefs.get(cat, "HEB")
                items.append({"item":p,"store":store,"category":cat})
        # Subtract pantry
        from utils.pantry import subtract_pantry
        items = subtract_pantry(items, state.get("pantry", []))
        items_df = pd.DataFrame(items) if items else pd.DataFrame([{"item":"(Everything covered by pantry or no parsed items)","store":"HEB","category":"pantry"}])
        st.dataframe(items_df, use_container_width=True)

        # Cost estimate
        from utils.pricing import load_prices, estimate_cost
        prices_df = load_prices()
        line_costs, totals = estimate_cost(items_df, prices_df)
        st.markdown("**Estimated costs by line & store:**")
        st.dataframe(line_costs, use_container_width=True)
        st.write(f"**Totals** → H‑E‑B: ${totals['HEB']:.2f} | Costco: ${totals['Costco']:.2f} | Aldi: ${totals['Aldi']:.2f}")

        # H‑E‑B prefill
        st.markdown("**H‑E‑B pre‑fill list (copy/paste):**")
        st.code(heb_prefill_text(items_df))

        # MFP CSV
        path = "data/mfp_export.csv"
        if st.button("Create CSV for MyFitnessPal"):
            make_mfp_csv(sel, path)
            with open(path,"rb") as f:
                st.download_button("Download mfp_export.csv", f, file_name="mfp_export.csv")
    else:
        st.info("Select recipes above to generate lists and exports.")

# ---------- Batch‑Prep Guide ----------
with tabs[6]:
    st.subheader("Batch‑Prep Guide")
    chosen = st.multiselect("Select recipes to prep", recipes_df["title"].tolist())
    if chosen:
        subset = recipes_df[recipes_df["title"].isin(chosen)]
        from collections import defaultdict
        tasks = defaultdict(int)
        for _, r in subset.iterrows():
            ings = str(r.get('ingredients','')).lower()
            if 'chicken' in ings: tasks['Cook chicken (batch)'] += 1
            if any(x in ings for x in ['rice','quinoa']): tasks['Cook grains (batch)'] += 1
            if any(x in ings for x in ['broccoli','pepper','onion','carrot']): tasks['Chop vegetables'] += 1
            if any(x in ings for x in ['yogurt','sauce']): tasks['Mix sauces/dressings'] += 1
        plan = [
            ("Weekend Prep", [
                ("Cook chicken (batch)", tasks['Cook chicken (batch)']*15),
                ("Cook grains (batch)", tasks['Cook grains (batch)']*12),
                ("Chop vegetables", tasks['Chop vegetables']*10),
            ]),
            ("Midweek Touch‑ups", [
                ("Mix sauces/dressings", tasks['Mix sauces/dressings']*8),
                ("Reheat & assemble", 20),
            ])
        ]
        for section, task_list in plan:
            st.markdown(f"### {section}")
            for name, minutes in task_list:
                if minutes>0: st.write(f"• {name} — ~{int(minutes)} min")
        st.caption("Time estimates are rough; tune rules in utils/prep.py as you go.")
    else:
        st.info("Pick some recipes to see combined prep tasks.")

# ---------- Store Cadence & Prices ----------
with tabs[7]:
    st.subheader("Store cadence & price map")
    sc = state["settings"]["store_cadence"]
    c1,c2 = st.columns(2)
    with c1: sc["costco_every_n_weeks"] = st.number_input("Costco trip every N weeks", 1, 12, sc.get("costco_every_n_weeks",4))
    with c2:
        sk = sc.get("skip_this_week", {"Costco":False,"Aldi":False})
        sk["Costco"] = st.toggle("Skip Costco this week", value=sk.get("Costco",False))
        sk["Aldi"]   = st.toggle("Skip Aldi this week", value=sk.get("Aldi",False))
        sc["skip_this_week"] = sk
    state["settings"]["store_cadence"]=sc; save_state(state)
    st.caption("Cadence will shape routing in future builds (e.g., bulk items only on Costco week).")
    st.markdown("### Edit price map (by keyword & store)")
    import pandas as pd
    prices = pd.read_csv("data/prices.csv")
    st.dataframe(prices, use_container_width=True)
    uploaded = st.file_uploader("Upload updated prices.csv", type=["csv"], key="prices_csv")
    if uploaded and st.button("Replace price map"):
        with open("data/prices.csv","wb") as f: f.write(uploaded.read())
        st.success("Replaced price map. Reload app to see changes.")
