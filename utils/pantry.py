import re
QTY_RE = re.compile(r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>cups?|tbsp|tsp|lb|lbs|oz|g|kg|can|cans)?\b", re.I)
UNIT_ALIASES={'lbs':'lb','pounds':'lb','pound':'lb','tbs':'tbsp','tablespoon':'tbsp','tablespoons':'tbsp','teaspoon':'tsp','teaspoons':'tsp',
             'cup':'cup','cups':'cup','ounce':'oz','ounces':'oz'}
def parse_qty_unit(text:str):
    m=QTY_RE.search(text); 
    if not m: return 1.0,''
    qty=float(m.group('qty')); unit=(m.group('unit') or '').lower(); unit=UNIT_ALIASES.get(unit,unit); return qty,unit
def normalize_name(text:str):
    s=text.lower(); return " ".join([w for w in re.sub(r"[^a-z0-9 ]","", s).split()[:2]])
def subtract_pantry(items, pantry):
    remaining=[]
    for it in items:
        name=normalize_name(it['item'])
        need_qty, need_unit = parse_qty_unit(it['item'])
        have_qty=0.0; have_unit=''
        for p in pantry:
            if normalize_name(p.get('item',''))==name:
                have_qty=float(p.get('quantity',0.0)); have_unit=(p.get('unit','') or '').lower(); break
        if have_qty>0 and (have_unit==need_unit or not have_unit or not need_unit):
            if have_qty>=need_qty: continue
            else:
                leftover=need_qty-have_qty
                it['item']=re.sub(QTY_RE, f"{leftover:g} {need_unit}".strip(), it['item']) if QTY_RE.search(it['item']) else f"{leftover:g} {need_unit} {it['item']}".strip()
        remaining.append(it)
    return remaining
