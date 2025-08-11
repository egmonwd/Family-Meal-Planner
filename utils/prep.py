from collections import defaultdict
def build_prep_tasks(recipes):
    # Very simple rules to demonstrate grouping
    tasks = defaultdict(int)
    for _, r in recipes.iterrows():
        title = r.get('title','')
        ings = str(r.get('ingredients','')).lower()
        if 'chicken' in ings: tasks['Cook chicken (batch)'] += 1
        if 'rice' in ings or 'quinoa' in ings: tasks['Cook grains (batch)'] += 1
        if any(x in ings for x in ['broccoli','pepper','onion','carrot']): tasks['Chop vegetables'] += 1
        if 'yogurt' in ings or 'sauce' in ings: tasks['Mix sauces/dressings'] += 1
    # Estimate minutes: each task instance ~10–20m
    plan = [
        ("Weekend Prep", [
            ("Cook chicken (batch)", tasks['Cook chicken (batch)']*15),
            ("Cook grains (batch)", tasks['Cook grains (batch)']*12),
            ("Chop vegetables", tasks['Chop vegetables']*10),
        ]),
        ("Midweek Touch-ups", [
            ("Mix sauces/dressings", tasks['Mix sauces/dressings']*8),
            ("Reheat & assemble", 20),
        ])
    ]
    return plan
