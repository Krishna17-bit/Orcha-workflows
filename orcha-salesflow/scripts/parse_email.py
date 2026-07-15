import os
import re
import sys
import json

def clean_value(val):
    if not val:
        return None
    val = val.strip().strip("-").strip(":").strip()
    return val

def parse_email_text(file_path):
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}", "confidence": 0.0}
        
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract ID from filename if possible
    base_name = os.path.basename(file_path)
    match_id = re.search(r"lead_email_(\d+)", base_name)
    lead_id = f"LEAD-{match_id.group(1)}" if match_id else "LEAD-UNKNOWN"

    data = {
        "lead_id": lead_id,
        "company_name": None,
        "contact_name": None,
        "email": None,
        "phone": None,
        "requirement": None,
        "budget": None,
        "urgency": None,
        "timeline": None,
        "source": "Unknown",
        "attachment_reference": None
    }

    # Extract From header details
    from_match = re.search(r"From:\s*([^<\n]+)(?:<([^>\n]+)>)?", content, re.IGNORECASE)
    if from_match:
        name_part = from_match.group(1).strip()
        email_part = from_match.group(2)
        if email_part:
            data["contact_name"] = name_part
            data["email"] = email_part.strip()
        else:
            if "@" in name_part:
                data["email"] = name_part
            else:
                data["contact_name"] = name_part

    # Company Name extraction
    company_match = re.search(r"(?:Company Name|Company):\s*(.*)", content, re.IGNORECASE)
    if company_match:
        data["company_name"] = clean_value(company_match.group(1))
    else:
        # Fallback to subject line pattern
        subj_match = re.search(r"Subject:.*-\s*(.*)", content, re.IGNORECASE)
        if subj_match:
            data["company_name"] = clean_value(subj_match.group(1))

    # Contact details fallbacks
    contact_match = re.search(r"(?:Contact Name|Contact):\s*(.*)", content, re.IGNORECASE)
    if contact_match:
        data["contact_name"] = clean_value(contact_match.group(1))

    email_match = re.search(r"(?:Contact Email|Email):\s*([\w\.-]+@[\w\.-]+\.\w+)", content, re.IGNORECASE)
    if email_match:
        data["email"] = clean_value(email_match.group(1))

    phone_match = re.search(r"(?:Contact Phone|Phone):\s*([+\d\s\(\)-]+)", content, re.IGNORECASE)
    if phone_match:
        data["phone"] = clean_value(phone_match.group(1))

    # Project parameters
    req_match = re.search(r"(?:Service Requirement|Service Requested|Service):\s*(.*)", content, re.IGNORECASE)
    if req_match:
        data["requirement"] = clean_value(req_match.group(1))

    budget_match = re.search(r"(?:Est\.?\s*Budget(?:\s*Limit)?|Target\s*Budget|Budget):\s*(.*)", content, re.IGNORECASE)
    if budget_match:
        budget_str = clean_value(budget_match.group(1))
        # Search for digits
        nums = re.findall(r"\d[\d,]*", budget_str)
        if nums:
            clean_num = nums[0].replace(",", "")
            try:
                data["budget"] = float(clean_num)
            except ValueError:
                data["budget"] = budget_str
        else:
            if "tbd" in budget_str.lower() or "pending" in budget_str.lower():
                data["budget"] = None
            else:
                data["budget"] = budget_str

    urgency_match = re.search(r"(?:Project Urgency|Urgency):\s*(.*)", content, re.IGNORECASE)
    if urgency_match:
        data["urgency"] = clean_value(urgency_match.group(1))

    timeline_match = re.search(r"(?:Delivery Timeline|Expected Timeline|Timeline|Duration):\s*(.*)", content, re.IGNORECASE)
    if timeline_match:
        data["timeline"] = clean_value(timeline_match.group(1))

    source_match = re.search(r"(?:Source|Lead Source):\s*(.*)", content, re.IGNORECASE)
    if source_match:
        data["source"] = clean_value(source_match.group(1))

    # Attachment detection
    attach_match = re.search(r"(?:Attached|Attachment|Attachment Reference):\s*(.*)", content, re.IGNORECASE)
    if attach_match:
        data["attachment_reference"] = clean_value(attach_match.group(1))
    else:
        # scan for text file endings in content
        txt_files = re.findall(r"([\w_]+\.txt)", content)
        filtered = [f for f in txt_files if not f.startswith("lead_email_")]
        if filtered:
            data["attachment_reference"] = filtered[0]

    # Calculate Parser Confidence
    filled_fields = sum(1 for k, v in data.items() if v is not None)
    total_fields = len(data)
    critical_missing = not data["email"] or not data["company_name"]
        
    confidence = (filled_fields / total_fields) * 100.0
    if critical_missing:
        confidence -= 30.0
    confidence = max(0.0, min(100.0, confidence))
    
    data["parser_confidence"] = round(confidence, 2)
    return data

if __name__ == "__main__":
    # Standard terminal node invocation printout
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No file path provided"}))
        sys.exit(1)
        
    file_path = sys.argv[1]
    parsed_data = parse_email_text(file_path)
    print(json.dumps(parsed_data, indent=2))
