
import streamlit as st, pandas as pd, json, os, uuid
from utils.mfp import make_mfp_csv
from utils.heb import heb_prefill_text
from utils.stores import split_by_store

DATA_PATH = "data/app_state.json"
RECIPES_CSV = "data/recipes.csv"
UPLOAD_DIR = "data/uploads"

st.set_page_config(page_title="Family Meal Planner — Milestone D", layout="wide")

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

st.title("🍽️ Family Meal Planner — Milestone D")

tabs = st.tabs(["Recipe Library","Pantry","Shopping & Exports"])

# ---------------- Recipe Library with URL import + OCR ----------------
with tabs[0]:
    st.subheader("Your Recipe Library")
    st.dataframe(recipes_df[["title","servings","store_tag","favorite","rating","est_cal","est_protein","est_carbs","est_fat","source_url"]], use_container_width=True)

    st.markdown("### Add Recipe")
    add_mode = st.radio("Add by", ["Link (auto-scrape)","Paste text","Upload file (PDF/Image/TXT)"])

    title = st.text_input("Title (optional, will use page title if blank)")
    servings = st.number_input("Servings", 1, 20, 4)
    store_tag = st.selectbox("Default store", ["HEB","Costco","Aldi"])
    favorite = st.toggle("Mark as favorite", value=False)
    rating = st.slider("Rating", 0, 5, 0)

    ingredients = ""
    steps = ""
    source_url = ""

    if add_mode == "Link (auto-scrape)":
        url = st.text_input("Recipe URL")
        if st.button("Import from URL"):
            try:
                from utils.recipe_import import import_from_url
                rec = import_from_url(url)
                if not title:  # if user didn't override
                    title = rec["title"]
                ingredients = rec["ingredients"]
                steps = rec["steps"]
                servings = rec["servings"]
                photo = rec["photo"]
                source_url = rec["source_url"]
                est_cal = rec["est_cal"]; est_pro = rec["est_protein"]; est_carb = rec["est_carbs"]; est_fat = rec["est_fat"]
                # write straight to library
                new = {
                    "title": title or rec["title"], "ingredients": ingredients, "steps": steps, "servings": servings,
                    "store_tag": store_tag, "photo": photo or "", "favorite": favorite, "rating": rating,
                    "est_cal": est_cal, "est_protein": est_pro, "est_carbs": est_carb, "est_fat": est_fat, "source_url": source_url
                }
                recipes_df.loc[len(recipes_df)] = new
                save_recipes_df(recipes_df)
                st.success(f"Imported “{new['title']}” from URL.")
            except Exception as e:
                st.error(f"URL import failed: {e}")
    elif add_mode == "Paste text":
        ingredients = st.text_area("Ingredients (one line per item or `;` separated)")
        steps = st.text_area("Steps")
        est_cal = st.number_input("Est. calories/serving", 0, 2000, 400)
        est_pro = st.number_input("Est. protein g/serving", 0, 200, 30)
        est_carb = st.number_input("Est. carbs g/serving", 0, 300, 35)
        est_fat = st.number_input("Est. fat g/serving", 0, 150, 14)
        if st.button("Add to Library"):
            new = {
                "title": title or "Untitled", "ingredients": ingredients, "steps": steps, "servings": servings,
                "store_tag": store_tag, "photo": "", "favorite": favorite, "rating": rating,
                "est_cal": est_cal, "est_protein": est_pro, "est_carbs": est_carb, "est_fat": est_fat, "source_url": ""
            }
            recipes_df.loc[len(recipes_df)] = new
            save_recipes_df(recipes_df); st.success("Recipe added.")
    else:
        up = st.file_uploader("Upload PDF/Image/TXT", type=["pdf","png","jpg","jpeg","txt"])
        if up is not None:
            fname = f"{uuid.uuid4().hex}_{up.name}"
            path = os.path.join("data/uploads", fname)
            with open(path, "wb") as f: f.write(up.read())
            st.success(f"Saved file: {fname}")
            # Try to parse text
            text = ""
            try:
                if fname.lower().endswith(".pdf"):
                    from utils.ocr import extract_pdf_text
                    text = extract_pdf_text(path)
                elif fname.lower().endswith(".txt"):
                    with open(path, "r", encoding="utf-8", errors="ignore") as rf:
                        text = rf.read()
                else:
                    # Image OCR via OCR.space if key present
                    api_key = None
                    try:
                        import streamlit as stlib
                        api_key = stlib.secrets.get("OCR_SPACE_API_KEY", None)
                    except Exception:
                        api_key = None
                    if api_key:
                        from utils.ocr import ocr_image_via_ocrspace
                        with open(path, "rb") as imgf:
                            text = ocr_image_via_ocrspace(imgf.read(), api_key)
                    else:
                        st.info("No OCR key set; paste ingredients/steps manually from your image.")
            except Exception as e:
                st.warning(f"OCR/Text extraction error: {e}")

            st.text_area("Extracted text (edit as needed)", value=text, height=200)
            ingredients = st.text_area("Ingredients (paste from text)", value="")
            steps = st.text_area("Steps (paste from text)", value="")
            est_cal = st.number_input("Est. calories/serving", 0, 2000, 400, key="file_cal")
            est_pro = st.number_input("Est. protein g/serving", 0, 200, 30, key="file_pro")
            est_carb = st.number_input("Est. carbs g/serving", 0, 300, 35, key="file_carb")
            est_fat = st.number_input("Est. fat g/serving", 0, 150, 14, key="file_fat")
            if st.button("Add to Library", key="file_add"):
                new = {
                    "title": title or up.name, "ingredients": ingredients, "steps": steps, "servings": servings,
                    "store_tag": store_tag, "photo": "", "favorite": favorite, "rating": rating,
                    "est_cal": est_cal, "est_protein": est_pro, "est_carbs": est_carb, "est_fat": est_fat, "source_url": ""
                }
                recipes_df.loc[len(recipes_df)] = new
                save_recipes_df(recipes_df); st.success("Recipe added.")

# ---------------- Pantry ----------------
with tabs[1]:
    st.subheader("Pantry — on‑hand items")
    pantry = state.get("pantry", [])
    c1,c2,c3 = st.columns(3)
    with c1: p_item = st.text_input("Item (e.g., chicken breast)")
    with c2: p_qty = st.number_input("Quantity", 0.0, 9999.0, 1.0, step=0.5)
    with c3: p_unit = st.text_input("Unit (e.g., lb, cup, can)", value="")
    if st.button("Add pantry item"):
        pantry.append({"item": p_item, "quantity": p_qty, "unit": p_unit})
        state["pantry"]=pantry; save_state(state); st.success("Added to pantry.")
    if pantry:
        st.table(pd.DataFrame(pantry))

# ---------------- Shopping & Exports ----------------
with tabs[2]:
    st.subheader("Build Shopping List (pantry-aware)")
    selected = st.multiselect("Choose recipes for this week", recipes_df["title"].tolist())
    if selected:
        sel = recipes_df[recipes_df["title"].isin(selected)].copy()
        items=[]
        for _,r in sel.iterrows():
            parts=[x.strip() for x in str(r["ingredients"]).replace("\\n",";").split(";") if x.strip()]
            for p in parts:
                items.append({"item":p,"store":r.get("store_tag","HEB"),"category":"pantry"})
        items_df = pd.DataFrame(items) if items else pd.DataFrame([{"item":"(No parsed items)","store":"HEB","category":"pantry"}])

        # Pantry subtraction (simple contains)
        pantry = state.get("pantry", [])
        to_buy = []
        for _, row in items_df.iterrows():
            item_txt = row["item"].lower()
            matched = any(p["item"].lower() in item_txt for p in pantry if p.get("item"))
            if matched: continue
            to_buy.append(row.to_dict())
        buy_df = pd.DataFrame(to_buy) if to_buy else pd.DataFrame([{"item":"(Everything found in pantry or no parsed items)","store":"HEB","category":"pantry"}])

        from utils.heb import heb_prefill_text
        st.markdown("**H‑E‑B pre‑fill list (copy/paste):**")
        st.code(heb_prefill_text(buy_df))

        st.markdown("**Export to MyFitnessPal (CSV)**")
        path = "data/mfp_export.csv"
        if st.button("Create CSV for MFP"):
            make_mfp_csv(sel, path)
            with open(path,"rb") as f:
                st.download_button("Download mfp_export.csv", f, file_name="mfp_export.csv")
    else:
        st.info("Select recipes above to generate lists and exports.")
