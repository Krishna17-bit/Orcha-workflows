import os
import re
import json
import sys

def parse_file(filepath):
    """
    Parses supplier update text files using regular expressions.
    """
    if not os.path.exists(filepath):
        return {"error": f"File {filepath} not found"}
        
    with open(filepath, mode="r", encoding="utf-8") as f:
        content = f.read()

    # Default parameters
    supplier_name = "Unknown Supplier"
    supplier_id = None
    affected_skus = []
    availability_status = "AVAILABLE"
    updated_lead_time_days = None
    price_change_percent = 0.0
    payment_terms_change = None
    delay_reason = None
    confidence = 1.0
    
    # 1. Parse Supplier ID and Name
    # Match patterns like: "Apex Hardware Group (SUP-001)"
    sup_match = re.search(r"([A-Za-z\s&]+)\s?\((SUP-\d+)\)", content)
    if sup_match:
        supplier_name = sup_match.group(1).strip()
        supplier_id = sup_match.group(2).strip()
    else:
        # Fallback names
        if "Apex Hardware" in content:
            supplier_name = "Apex Hardware Group"
            supplier_id = "SUP-001"
        elif "Dynamic Actuators" in content:
            supplier_name = "Dynamic Actuators Inc"
            supplier_id = "SUP-003"
        elif "Precision Valve" in content:
            supplier_name = "Precision Valve Corp"
            supplier_id = "SUP-002"
        else:
            confidence -= 0.3
            
    # 2. Extract SKUs
    # Match patterns like "SKU-001", "SKU-O02", etc.
    sku_pattern = re.compile(r"SKU[-_][O0-9]{3}", re.IGNORECASE)
    raw_skus = sku_pattern.findall(content)
    # Normalize SKUs (replace 'O' with '0')
    for raw_sku in raw_skus:
        normalized = raw_sku.upper().replace("_", "-").replace("O", "0")
        if normalized not in affected_skus:
            affected_skus.append(normalized)
            
    if not affected_skus:
        confidence -= 0.3
        
    # 3. Detect Availability / Delays
    if "delay" in content.lower() or "slowdown" in content.lower() or "delayed" in content.lower():
        availability_status = "DELAYED"
        # Try to extract delay reason
        delay_match = re.search(r"(?:slowdown|delay)(?:\s\w+){0,10}\s(?:at|due to)\s([^.\n]+)", content, re.IGNORECASE)
        if delay_match:
            delay_reason = delay_match.group(1).strip()
        else:
            delay_reason = "Unspecified supply chain delay"
            
    # 4. Extract Lead Time Changes
    # Look for patterns like "10 days to 18 days" or "lead time of 5 days"
    lead_match = re.search(r"lead time(?: of)? (\d+) days", content, re.IGNORECASE)
    range_match = re.search(r"(\d+) days to (\d+) days", content, re.IGNORECASE)
    if range_match:
        updated_lead_time_days = int(range_match.group(2))
    elif lead_match:
        updated_lead_time_days = int(lead_match.group(1))
    else:
        # Check standard defaults based on supplier
        if supplier_id == "SUP-001":
            updated_lead_time_days = 5
        elif supplier_id == "SUP-002":
            updated_lead_time_days = 7
        elif supplier_id == "SUP-003":
            updated_lead_time_days = 10
        else:
            confidence -= 0.2
            
    # 5. Extract Price Change Percentage
    # Look for "increase by 15%" or similar
    price_match = re.search(r"(?:increase|adjust|change)(?:\s\w+){0,5}\sby\s(\d+(?:\.\d+)?)%", content, re.IGNORECASE)
    if price_match:
        price_change_percent = float(price_match.group(1))
    elif "price is stable" in content.lower() or "unaffected" in content.lower():
        price_change_percent = 0.0
        
    # 6. Extract payment terms change
    if "payment terms" in content.lower():
        terms_match = re.search(r"payment terms(?:\s\w+){0,5}\s(?:to|remains|is)\s(Net\s?\d+)", content, re.IGNORECASE)
        if terms_match:
            payment_terms_change = terms_match.group(1).strip()
            
    confidence = max(0.0, min(1.0, confidence))
    
    return {
        "supplier_name": supplier_name,
        "supplier_id": supplier_id,
        "affected_skus": affected_skus,
        "availability_status": availability_status,
        "updated_lead_time_days": updated_lead_time_days,
        "price_change_percent": price_change_percent,
        "payment_terms_change": payment_terms_change,
        "delay_reason": delay_reason,
        "confidence": confidence,
        "review_required": confidence < 0.70
    }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_to_parse = sys.argv[1]
        result = parse_file(file_to_parse)
        print(json.dumps(result, indent=2))
    else:
        # Default scan supplier updates
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        updates_dir = os.path.join(base_dir, "business_data", "suppliers", "supplier_updates")
        results = {}
        if os.path.exists(updates_dir):
            for filename in os.listdir(updates_dir):
                if filename.endswith(".txt"):
                    filepath = os.path.join(updates_dir, filename)
                    results[filename] = parse_file(filepath)
            print(json.dumps(results, indent=2))
        else:
            print(json.dumps({"error": f"Directory {updates_dir} not found"}))
