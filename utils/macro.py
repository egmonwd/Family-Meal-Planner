import math

def per_dinner_targets(profile, dinner_calorie_fraction=0.35):
    return {
        'cal': profile.get('calories',2200)*dinner_calorie_fraction,
        'p': profile.get('protein_g',170)*dinner_calorie_fraction,
        'c': profile.get('carbs_g',180)*dinner_calorie_fraction,
        'f': profile.get('fat_g',70)*dinner_calorie_fraction,
    }

def score_recipe_to_targets(row, targets):
    serv=max(int(row.get('servings',1)),1)
    cal=float(row.get('est_cal',0))/serv
    p=float(row.get('est_protein',0))/serv
    c=float(row.get('est_carbs',0))/serv
    f=float(row.get('est_fat',0))/serv
    w_cal,w_p,w_c,w_f = 0.5, 2.0, 1.0, 1.0
    d=( (cal-targets['cal'])**2*w_cal + (p-targets['p'])**2*w_p + (c-targets['c'])**2*w_c + (f-targets['f'])**2*w_f )**0.5
    return d
