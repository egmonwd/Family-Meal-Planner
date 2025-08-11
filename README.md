# Family Meal Planner — Milestone E+ (Merged)
This build merges **all** features from earlier milestones (A–D) plus E enhancements:
- Multi‑profiles, daily headcount, full‑week generator (Breakfast/Lunch/Snack/Dinner)
- Favorites‑first planner, macro splits, quota guard, Library‑only fallback
- Wider search (themes + pagination) via Spoonacular; ingredient parsing
- Recipe Library: add by link (auto‑scrape), paste text, or upload file (PDF/Image/TXT)
- Auto nutrition fill via Spoonacular when macros are missing
- Pantry (quantity‑aware), H‑E‑B prefill, MyFitnessPal CSV
- Batch‑Prep Guide
- Store preferences by category; store cadence flags; simple price map & cost estimate

## Secrets (Streamlit → ⋯ → Settings → Secrets)
SPOONACULAR_API_KEY = "your-key"
# Optional, for image OCR (PDFs do not need this):
OCR_SPACE_API_KEY = "your-ocrspace-key"
