# Family Meal Planner — Milestone D (Streamlit)

Adds on top of Milestone C:
- **URL Importer** using `recipe-scrapers` for hundreds of popular recipe sites.
- **OCR pipeline**:
  - PDFs: parsed with `pdfplumber` (no external API needed).
  - Images (jpg/png): optional **OCR.space** API (set `OCR_SPACE_API_KEY` in Secrets) for cloud OCR.
- Respects existing features: favorites-first, pantry-aware shopping, batch-prep, quota guard.

## Secrets
- `SPOONACULAR_API_KEY` — for auto-generation and optional nutrition analysis.
- `OCR_SPACE_API_KEY` — optional, for image OCR (PDFs do not require this).

## Notes
- Nutrition fields from URL imports depend on the source site. If missing, you can keep your Spoonacular key for generation or add a nutrition API later.
