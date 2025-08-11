import pandas as pd

def make_mfp_csv(recipes_df, path):
    records = []
    for _, r in recipes_df.iterrows():
        records.append({
            'name': r['title'],
            'serving_size': f"1 of {int(r['servings'])} servings",
            'calories': r['est_cal'],
            'protein_g': r['est_protein'],
            'carbs_g': r['est_carbs'],
            'fat_g': r['est_fat']
        })
    pd.DataFrame(records).to_csv(path, index=False)
    return path
