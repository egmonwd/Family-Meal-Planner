def heb_prefill_text(df):
    import pandas as pd
    if df is None or (isinstance(df,pd.DataFrame) and df.empty):
        return "H‑E‑B Shopping List:\n(No items)"
    if isinstance(df, pd.DataFrame):
        lines=[f"- {row['item']}" for _,row in df.iterrows()]
    else:
        lines=[]
    return "H‑E‑B Shopping List:\n"+ "\n".join(lines)
