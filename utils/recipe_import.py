from recipe_scrapers import scrape_me

def import_from_url(url: str) -> dict:
    scraper = scrape_me(url, wild_mode=True)
    title = scraper.title() or "Imported Recipe"
    try:
        servings = int(scraper.yields().split()[0])
    except Exception:
        servings = 4
    ing_list = scraper.ingredients() or []
    steps_list = scraper.instructions_list() or [scraper.instructions() or ""]
    image = scraper.image() or ""
    nutrients = {}
    try:
        nutrients = scraper.nutrients()
    except Exception:
        nutrients = {}

    # Flatten ingredients & steps
    ingredients = "; ".join([i.strip() for i in ing_list if i and isinstance(i, str)])
    steps = "\n".join([s.strip() for s in steps_list if s and isinstance(s, str)])

    # Macros if provided
    cal = nutrients.get("calories") or 0
    protein = nutrients.get("protein") or 0
    carbs = nutrients.get("carbohydrate") or nutrients.get("carbohydrates") or 0
    fat = nutrients.get("fat") or 0

    return {
        "title": title,
        "servings": servings,
        "ingredients": ingredients,
        "steps": steps,
        "photo": image,
        "est_cal": cal if isinstance(cal,(int,float)) else 0,
        "est_protein": protein if isinstance(protein,(int,float)) else 0,
        "est_carbs": carbs if isinstance(carbs,(int,float)) else 0,
        "est_fat": fat if isinstance(fat,(int,float)) else 0,
        "source_url": url
    }
