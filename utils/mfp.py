import pandas as pd

def make_mfp_csv(df, path):
    rows=[]
    for _,r in df.iterrows():
        rows.append({'name':r['title'],'serving_size':f"1 of {int(r.get('servings',1))} servings",'calories':r.get('est_cal',0),'protein_g':r.get('est_protein',0),'carbs_g':r.get('est_carbs',0),'fat_g':r.get('est_fat',0)})
    pd.DataFrame(rows).to_csv(path,index=False)
    return path
