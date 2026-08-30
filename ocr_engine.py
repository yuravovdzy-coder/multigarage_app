"""
ocr_engine.py
Image -> text -> structured field extraction.

Pydroid 3 note: pytesseract needs the native `tesseract` binary, which is
not bundled with Pydroid 3 by default. This module is written to degrade
gracefully:
  1. It first tries pytesseract (works if the user installs the Tesseract
     APK/binary separately, e.g. via Termux-style native builds).
  2. If that import/run fails, it returns an empty result so the calling
     screen simply falls back to manual entry instead of crashing the app.

Install on Pydroid 3 (Terminal inside the app):
    pip install pytesseract pillow
A native tesseract binary is still required for real OCR; without it,
extract_text() returns "" and the UI asks the user to type the values.
"""

import re
import datetime

try:
    import pytesseract
    from PIL import Image, ImageOps, ImageFilter
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False


def preprocess_image(path):
    """Grayscale + contrast boost + light sharpen, improves OCR accuracy
    on phone-camera receipt photos."""
    img = Image.open(path)
    img = ImageOps.exif_transpose(img)
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.SHARPEN)
    return img


def extract_text(path):
    """Returns raw OCR text, or '' if OCR isn't available on this device."""
    if not OCR_AVAILABLE:
        return ""
    try:
        img = preprocess_image(path)
        return pytesseract.image_to_string(img, lang="ukr+eng")
    except Exception:
        return ""


# ---------------------------------------------------------------- parsing

DATE_PATTERNS = [
    r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})\b",
    r"\b(\d{4})[./-](\d{1,2})[./-](\d{1,2})\b",
]

AMOUNT_PATTERN = r"(\d{1,3}(?:[ .,]\d{3})*[.,]\d{2})\s*(?:грн|uah|₴|\$|usd|€)?"
ODOMETER_PATTERN = r"\b(\d{2,3}[ ,]?\d{3})\s*(?:km|км)\b"
PART_NUMBER_PATTERN = r"\b([A-Z0-9]{2,}[-][A-Z0-9]{2,}(?:[-][A-Z0-9]+)?)\b"


def extract_date(text):
    for pat in DATE_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if not m:
            continue
        groups = [int(g) for g in m.groups()]
        try:
            if groups[0] > 31:  # YYYY-MM-DD
                y, mo, d = groups
            else:  # DD-MM-YYYY
                d, mo, y = groups
                if y < 100:
                    y += 2000
            return datetime.date(y, mo, d).isoformat()
        except ValueError:
            continue
    return None


def extract_amount(text):
    matches = re.findall(AMOUNT_PATTERN, text, re.IGNORECASE)
    if not matches:
        return None
    # take the largest plausible amount on the receipt (usually the total)
    values = []
    for m in matches:
        cleaned = m.replace(" ", "").replace(",", ".")
        # normalize "1.234.56" style thousands separators
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = "".join(parts[:-1]) + "." + parts[-1]
        try:
            values.append(float(cleaned))
        except ValueError:
            continue
    return max(values) if values else None


def extract_odometer(text):
    m = re.search(ODOMETER_PATTERN, text, re.IGNORECASE)
    if m:
        return int(m.group(1).replace(" ", "").replace(",", ""))
    # fallback: a bare 4-6 digit number is a common odometer photo pattern
    m = re.search(r"\b(\d{4,6})\b", text)
    return int(m.group(1)) if m else None


def extract_part_number(text):
    m = re.search(PART_NUMBER_PATTERN, text)
    return m.group(1) if m else None


def parse_receipt(path):
    """
    High-level helper used by every 'Camera/Photo' button in the app.
    Returns a dict with whatever fields could be confidently extracted;
    missing keys mean 'let the user fill this in manually'.
    """
    text = extract_text(path)
    if not text:
        return {"ocr_available": OCR_AVAILABLE, "raw_text": "", "date": None,
                "amount": None, "odometer": None, "part_number": None}

    return {
        "ocr_available": True,
        "raw_text": text,
        "date": extract_date(text),
        "amount": extract_amount(text),
        "odometer": extract_odometer(text),
        "part_number": extract_part_number(text),
    }
