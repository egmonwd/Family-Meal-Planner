from recipe_scrapers import scrape_me
def import_from_url(url: str) -> dict:
    sc = scrape_me(url, wild_mode=True)
    title = sc.title() or "Imported Recipe"
    try: servings=int((sc.yields() or '4').split()[0])
    except Exception: servings=4
    ing = sc.ingredients() or []
    steps_list = sc.instructions_list() or [sc.instructions() or ""]
    image = sc.image() or ""
    try: nutrients=sc.nutrients()
    except Exception: nutrients={}
    ingredients="; ".join([i.strip() for i in ing if isinstance(i,str) and i.strip()])
    steps="\n".join([s.strip() for s in steps_list if isinstance(s,str) and s.strip()])
    cal=nutrients.get("calories") or 0; pro=nutrients.get("protein") or 0
    carb=nutrients.get("carbohydrate") or nutrients.get("carbohydrates") or 0; fat=nutrients.get("fat") or 0
    return {"title":title,"servings":servings,"ingredients":ingredients,"steps":steps,"photo":image,
            "est_cal": cal if isinstance(cal,(int,float)) else 0,
            "est_protein": pro if isinstance(pro,(int,float)) else 0,
            "est_carbs": carb if isinstance(carb,(int,float)) else 0,
            "est_fat": fat if isinstance(fat,(int,float)) else 0, "source_url": url}
