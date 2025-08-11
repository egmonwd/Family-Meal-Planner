import pdfplumber, requests
def extract_pdf_text(path:str)->str:
    text=[]; 
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages: text.append(p.extract_text() or "")
    return "\n".join(text).strip()
def ocr_image_via_ocrspace(content:bytes, api_key:str)->str:
    url="https://api.ocr.space/parse/image"
    files={"file":("image.jpg",content)}; data={"apikey":api_key,"language":"eng","isOverlayRequired":False}
    r=requests.post(url, files=files, data=data, timeout=60); r.raise_for_status()
    js=r.json(); 
    if js.get("IsErroredOnProcessing"): raise RuntimeError(js.get("ErrorMessage") or "OCR failed")
    return "\n".join([p.get("ParsedText","") for p in js.get("ParsedResults",[])]) .strip()
