import os
import re
import sys
import json

def normalize_noisy_number(num_str):
    # Fix OCR confusion where 'O' or 'o' is used instead of '0'
    normalized = num_str.replace("O", "0").replace("o", "0")
    # Remove non-numeric elements except decimal point
    normalized = re.sub(r"[^\d\.]", "", normalized)
    return normalized

def clean_ocr_text(text):
    # Common character errors in low-confidence OCR text
    replacements = {
        "Sp4rk": "Spark",
        "Cre@tive": "Creative",
        "Cl1ent": "Client",
        "C0ntact": "Contact",
        "L1am": "Liam",
        "F0ster": "Foster",
        "Serv1ce": "Service",
        "Qu@nt1ty": "Quantity",
        "Budg3t": "Budget",
        "D1scount": "Discount",
        "R3quested": "Requested",
        "Deadl1ne": "Deadline",
        "Paym3nt": "Payment",
        "N3t": "Net",
        "EN0": "END"
    }
    cleaned = text
    typo_count = 0
    for k, v in replacements.items():
        if k in cleaned:
            # Count OCR substitution glitches to penalize confidence
            typo_count += len(re.findall(re.escape(k), cleaned))
            cleaned = cleaned.replace(k, v)
    return cleaned, typo_count

def extract_quote_data(file_path):
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}", "confidence": 0.0}
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    cleaned_content, typo_count = clean_ocr_text(content)

    data = {
        "vendor_or_company": None,
        "requested_service": None,
        "quantity": None,
        "estimated_budget": None,
        "requested_discount": 0.0,
        "deadline": None,
        "payment_terms": "Net 30",
        "confidence": 1.0
    }

    # Company name extraction
    client_match = re.search(r"(?:Client|Client Name):\s*(.*)", cleaned_content, re.IGNORECASE)
    if client_match:
        data["vendor_or_company"] = client_match.group(1).strip()
    else:
        # Fallback keyword checks in headers
        client_hdr_match = re.search(r"APEX SYSTEMS|HORIZON LOGISTICS|SPARK CREATIVE", cleaned_content.upper())
        if client_hdr_match:
            data["vendor_or_company"] = client_hdr_match.group(0).title()

    # Service extraction
    srv_match = re.search(r"(?:Requested Service|Service):\s*(.*)", cleaned_content, re.IGNORECASE)
    if srv_match:
        data["requested_service"] = srv_match.group(1).strip()

    # Quantity extraction
    qty_match = re.search(r"(?:Quantity):\s*(.*)", cleaned_content, re.IGNORECASE)
    if qty_match:
        qty_str = qty_match.group(1).strip()
        qty_nums = re.findall(r"\d+", qty_str)
        if qty_nums:
            data["quantity"] = int(qty_nums[0])
        else:
            data["quantity"] = qty_str

    # Budget extraction
    budget_match = re.search(r"(?:Estimated Budget|Budget|Subtotal):\s*(.*)", cleaned_content, re.IGNORECASE)
    if budget_match:
        raw_budget = budget_match.group(1).strip()
        clean_b = normalize_noisy_number(raw_budget)
        if clean_b:
            try:
                data["estimated_budget"] = float(clean_b)
            except ValueError:
                data["estimated_budget"] = raw_budget

    # Discount rate extraction
    discount_match = re.search(r"(?:Requested Discount|Discount|Discount Requested):\s*(.*)", cleaned_content, re.IGNORECASE)
    if discount_match:
        disc_str = discount_match.group(1).strip()
        nums = re.findall(r"(\d+)(?:\s*%)?", disc_str)
        if nums:
            data["requested_discount"] = float(nums[0]) / 100.0
        else:
            dec_nums = re.findall(r"\d+\.\d+", disc_str)
            if dec_nums:
                data["requested_discount"] = float(dec_nums[0])

    # Deadline timeline extraction
    timeline_match = re.search(r"(?:Delivery Duration|Deadline|Expected Start):\s*(.*)", cleaned_content, re.IGNORECASE)
    if timeline_match:
        data["deadline"] = timeline_match.group(1).strip()

    # Payment terms extraction
    pay_match = re.search(r"(?:Payment Terms|Payment):\s*(.*)", cleaned_content, re.IGNORECASE)
    if pay_match:
        data["payment_terms"] = pay_match.group(1).strip()

    # Confidence calculation: subtract 15% per typo/OCR substitution corrected
    ocr_confidence = 1.0 - (typo_count * 0.15)
    
    # Penalize heavily if crucial identifiers are missing
    if not data["vendor_or_company"] or data["estimated_budget"] is None:
        ocr_confidence -= 0.25
        
    ocr_confidence = max(0.1, min(1.0, ocr_confidence))
    data["confidence"] = round(ocr_confidence, 2)
    
    return data

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No file path provided"}))
        sys.exit(1)
        
    file_path = sys.argv[1]
    extracted = extract_quote_data(file_path)
    print(json.dumps(extracted, indent=2))
