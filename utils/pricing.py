import pandas as pd
def load_prices(path='data/prices.csv'):
    try: return pd.read_csv(path)
    except Exception: return pd.DataFrame(columns=['keyword','HEB','Costco','Aldi','unit'])
def estimate_cost(items_df, prices_df):
    total={'HEB':0.0,'Costco':0.0,'Aldi':0.0}; line_costs=[]
    for _,row in items_df.iterrows():
        s=row['item'].lower(); match=None
        for _,pr in prices_df.iterrows():
            if pr['keyword'] in s: match=pr; break
        if match is not None:
            c_HEB=float(match.get('HEB',0.0)); c_C=float(match.get('Costco',0.0)); c_A=float(match.get('Aldi',0.0))
            store=row.get('store','HEB'); cost=c_HEB if store=='HEB' else c_C if store=='Costco' else c_A
            line_costs.append({'item':row['item'],'store':store,'est_cost':cost}); total[store]+=cost
        else:
            line_costs.append({'item':row['item'],'store':row.get('store','HEB'),'est_cost':0.0})
    return pd.DataFrame(line_costs), total
