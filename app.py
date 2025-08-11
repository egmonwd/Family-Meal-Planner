import streamlit as st
import pandas as pd
import json, os
from utils.nutrition import rough_estimate_from_text
from utils.mfp import make_mfp_csv
from utils.heb import heb_prefill_text
from utils.stores import split_by_store

DATA_PATH = "data/app_state.json"
RECIPES_CSV = "data/recipes.csv"

def load_state():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

def save_state(state):
    with open(DATA_PATH, "w") as f:
        json.dump(state, f, indent=2)

def load_recipes_df():
    if os.path.exists(RECIPES_CSV):
        return pd.read_csv(RECIPES_CSV)
    return pd.DataFrame(columns=["title","ingredients","steps","servings","store_tag","photo","favorite","rating","est_cal","est_protein","est_carbs","est_fat"])

state = load_state()
recipes_df = load_recipes_df()

st.title("Family Meal Planner — MVP")

st.subheader("Weekly Toggles")
state['profiles']['default']['ingredient_limit'] = st.slider("Max ingredients", 3, 20, state['profiles']['default']['ingredient_limit'])
state['profiles']['default']['max_prep_minutes'] = st.slider("Max prep time", 5, 90, state['profiles']['default']['max_prep_minutes'])
state['profiles']['default']['batch_pref'] = st.selectbox("Batch-prep preference", ["Low","Medium","High"], index=["Low","Medium","High"].index(state['profiles']['default']['batch_pref']))
save_state(state)

st.subheader("Recipe Library")
if st.button("Add Sample Recipe"):
    new = {
        "title": "Test Meal",
        "ingredients": "item1; item2",
        "steps": "Step 1",
        "servings": 4,
        "store_tag": "HEB",
        "photo": "",
        "favorite": False,
        "rating": 0,
        "est_cal": 300,
        "est_protein": 25,
        "est_carbs": 20,
        "est_fat": 10
    }
    recipes_df.loc[len(recipes_df)] = new
    recipes_df.to_csv(RECIPES_CSV, index=False)
st.dataframe(recipes_df)

st.subheader("Shopping & Exports")
selected = st.multiselect("Choose recipes", recipes_df['title'].tolist())
if selected:
    sel_df = recipes_df[recipes_df['title'].isin(selected)]
    items = []
    for _, r in sel_df.iterrows():
        for ing in r['ingredients'].split(';'):
            items.append({"item": ing.strip(), "store": r['store_tag']})
    items_df = pd.DataFrame(items)
    buckets = split_by_store(items_df)
    st.text(heb_prefill_text(buckets.get("HEB", items_df)))
    if st.button("Export to MyFitnessPal CSV"):
        path = "data/mfp_export.csv"
        make_mfp_csv(sel_df, path)
        with open(path, "rb") as f:
            st.download_button("Download MFP CSV", f, file_name="mfp_export.csv")
