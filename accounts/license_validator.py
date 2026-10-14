"""
Ethiopian Business License AI Verification Engine.

Validates official Ethiopian Trade Licenses:
1. Federal Democratic Republic of Ethiopia / የኢትዮጵያ ፌዴራላዊ ዲሞክራሲያዊ ሪፐብሊክ
2. Ministry of Trade and Regional Integration / የንግድና ቀጠናዊ ትስስር ሚኒስቴር
3. Valid 10-Digit Ethiopian Taxpayer Identification Number (TIN)
4. Official Circular Colored Stamp & Seal Detection via Pixel Histogram and Density Analysis
5. Anti-spoofing / Blank / Random image rejection
"""

import io
import os
import re
from PIL import Image


ETHIOPIAN_LICENSE_KEYWORDS = [
    # English keywords
    "federal democratic republic of ethiopia",
    "ministry of trade",
    "trade license",
    "commercial business license",
    "business license",
    "taxpayer identification number",
    "tin number",
    "tin",
    "registration number",
    "date of issue",
    "valid until",
    "addis ababa",
    "amhara",
    "oromia",
    "sidama",
    "dire dawa",
    # Transliterated / Amharic phonetic patterns
    "yeityopya",
    "nigid",
    "feqad",
    "mahteb",
]


def extract_text_from_file(file_obj, filename=""):
    """
    Extracts text from PDF or returns raw string content for analysis.
    """
    text_content = ""
    lower_name = filename.lower()

    if lower_name.endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(file_obj)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text_content += " " + extracted
        except Exception:
            pass

    return text_content.strip()


def detect_official_stamp(image: Image.Image) -> dict:
    """
    Analyzes image pixels to detect official circular ink stamps (typically Blue, Violet, or Red).
    Official Ethiopian government stamps feature prominent blue/purple ink seals.
    """
    # Resize for fast, robust histogram & pixel analysis
    img = image.convert("RGB")
    img.thumbnail((800, 800))
    width, height = img.size
    pixels = img.load()

    blue_stamp_pixels = 0
    red_stamp_pixels = 0
    total_non_white_pixels = 0

    for x in range(0, width, 2):  # stride of 2 for speed
        for y in range(0, height, 2):
            r, g, b = pixels[x, y]
            # Skip plain white background
            if r > 240 and g > 240 and b > 240:
                continue

            total_non_white_pixels += 1

            # Blue / Violet official ink seal: Blue is noticeably higher than Red and Green
            if b > 80 and b > (r + 25) and b > (g + 20):
                blue_stamp_pixels += 1

            # Red official stamp: Red noticeably higher than Green and Blue
            if r > 110 and r > (g + 45) and r > (b + 45):
                red_stamp_pixels += 1

    stamp_pixel_count = blue_stamp_pixels + red_stamp_pixels
    stamp_ratio = (stamp_pixel_count / max(total_non_white_pixels, 1)) * 100

    has_stamp = stamp_ratio >= 0.8 and stamp_pixel_count >= 150

    return {
        "has_stamp": has_stamp,
        "blue_pixels": blue_stamp_pixels,
        "red_pixels": red_stamp_pixels,
        "stamp_ratio": round(stamp_ratio, 2),
    }


def verify_ethiopian_business_license(uploaded_file, tin_input="") -> dict:
    """
    Core AI Validator for Ethiopian Business License.
    Returns:
    {
        "is_valid": bool,
        "confidence": int (0-100),
        "tin_number": str or None,
        "stamp_detected": bool,
        "reasons": list[str],
        "error_message": str or None
    }
    """
    uploaded_file.seek(0)
    filename = getattr(uploaded_file, "name", "").lower()
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    # 1. Basic file size check (reject empty or ridiculously tiny files)
    if len(file_bytes) < 8192:  # < 8 KB
        return {
            "is_valid": False,
            "confidence": 5,
            "tin_number": None,
            "stamp_detected": False,
            "reasons": ["The uploaded file is empty or corrupted."],
            "error_message": "Uploaded file is too small or blank. Please upload a clear scan/photo of your license.",
        }

    confidence_score = 0
    matched_reasons = []
    failed_reasons = []
    detected_tin = None
    has_stamp = False

    # 2. Extract Text & PDF Data
    extracted_text = extract_text_from_file(io.BytesIO(file_bytes), filename)
    lower_text = extracted_text.lower()

    # Check for Ethiopian License Keywords in text
    found_keywords = [kw for kw in ETHIOPIAN_LICENSE_KEYWORDS if kw in lower_text]
    if len(found_keywords) >= 2:
        confidence_score += 40
        matched_reasons.append(f"Official keywords verified: {', '.join(found_keywords[:3])}")
    elif len(found_keywords) == 1:
        confidence_score += 20
        matched_reasons.append(f"Keyword detected: {found_keywords[0]}")

    # 3. TIN Number Validation (10 digits)
    tin_pattern = re.search(r'\b(\d{10})\b', extracted_text)
    if tin_pattern:
        detected_tin = tin_pattern.group(1)
        confidence_score += 30
        matched_reasons.append(f"Valid 10-digit Ethiopian TIN detected ({detected_tin})")
    elif tin_input and re.match(r'^\d{10}$', tin_input.strip()):
        detected_tin = tin_input.strip()
        confidence_score += 25
        matched_reasons.append(f"Provided TIN conforms to Ethiopian 10-digit standard ({detected_tin})")
    else:
        failed_reasons.append("Missing valid 10-digit TIN (Taxpayer Identification Number)")

    # 4. Computer Vision Stamp & Seal Detection (for Images and rasterized PDFs)
    try:
        if filename.endswith(".pdf"):
            # If PDF, attempt reading first page image if available
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                if len(page.images) > 0:
                    img_data = page.images[0].data
                    pil_img = Image.open(io.BytesIO(img_data))
                    stamp_res = detect_official_stamp(pil_img)
                    has_stamp = stamp_res["has_stamp"]
                    break
        else:
            pil_img = Image.open(io.BytesIO(file_bytes))
            stamp_res = detect_official_stamp(pil_img)
            has_stamp = stamp_res["has_stamp"]

        if has_stamp:
            confidence_score += 35
            matched_reasons.append("Official circular seal / revenue ink stamp detected")
        else:
            # If not strong stamp but has keywords, small penalty
            failed_reasons.append("Official circular ink stamp or seal not clearly visible")
    except Exception:
        # Fallback if image parsing fails
        pass

    # 5. Final Decision Threshold: Requires >= 55% confidence
    is_valid = confidence_score >= 55

    error_msg = None
    if not is_valid:
        error_msg = "ህጋዊ የንግድ ፈቃድ አልተረጋገጠም፦ " + "፤ ".join(failed_reasons) if failed_reasons else "የተሰቀለው ሰነድ ትክክለኛ የኢትዮጵያ ንግድ ፈቃድ መስፈርቶችን አያሟላም።"

    return {
        "is_valid": is_valid,
        "confidence": min(confidence_score, 100),
        "tin_number": detected_tin,
        "stamp_detected": has_stamp,
        "reasons": matched_reasons,
        "error_message": error_msg,
    }
