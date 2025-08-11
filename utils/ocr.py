import os, requests, io
import pdfplumber

def extract_pdf_text(path: str) -> str:
    text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text() or "")
    return "\n".join(text).strip()

def ocr_image_via_ocrspace(content: bytes, api_key: str) -> str:
    url = "https://api.ocr.space/parse/image"
    files = {"file": ("image.jpg", content)}
    data = {"apikey": api_key, "language": "eng", "isOverlayRequired": False}
    r = requests.post(url, files=files, data=data, timeout=60)
    r.raise_for_status()
    js = r.json()
    if js.get("IsErroredOnProcessing"):
        raise RuntimeError(js.get("ErrorMessage") or "OCR failed")
    parsed = js.get("ParsedResults", [])
    return "\n".join([p.get("ParsedText","") for p in parsed]).strip()
