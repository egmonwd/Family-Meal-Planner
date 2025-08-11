def heb_prefill_text(df):
    lines=[f"- {row['item']}" for _,row in df.iterrows()]
    return "H‑E‑B Shopping List:\n"+ "\n".join(lines)
