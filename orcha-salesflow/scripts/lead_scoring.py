import sys
import json

def calculate_lead_score(email_data, quote_data=None):
    score = 0
    reason_codes = []
    
    # 1. Budget size weighting (Max 30 pts)
    budget = email_data.get("budget")
    if quote_data and quote_data.get("estimated_budget") is not None:
        budget = quote_data.get("estimated_budget")
        
    if budget is not None:
        try:
            budget_val = float(budget)
            if budget_val >= 100000:
                score += 30
                reason_codes.append("BUDGET_HIGH (+$30)")
            elif budget_val >= 50000:
                score += 20
                reason_codes.append("BUDGET_MID (+$20)")
            elif budget_val >= 10000:
                score += 10
                reason_codes.append("BUDGET_LOW (+$10)")
            else:
                score += 2
                reason_codes.append("BUDGET_MINIMAL (+$2)")
        except ValueError:
            score += 5
            reason_codes.append("BUDGET_UNPARSED (+$5)")
    else:
        score += 0
        reason_codes.append("BUDGET_MISSING (+0)")

    # 2. Urgency weighting (Max 20 pts)
    urgency = str(email_data.get("urgency", "")).lower()
    if any(k in urgency for k in ["high", "critical", "urgent", "immediate"]):
        score += 20
        reason_codes.append("URGENCY_HIGH (+$20)")
    elif any(k in urgency for k in ["medium", "normal", "60 days"]):
        score += 10
        reason_codes.append("URGENCY_MED (+$10)")
    else:
        score += 5
        reason_codes.append("URGENCY_LOW (+$5)")

    # 3. Completeness of Lead Data (Max 20 pts)
    missing_fields = []
    for f in ["company_name", "contact_name", "email", "requirement"]:
        if not email_data.get(f):
            missing_fields.append(f)
            
    if not missing_fields:
        score += 20
        reason_codes.append("COMPLETE_DATA (+$20)")
    else:
        penalty = len(missing_fields) * 5
        score += max(0, 20 - penalty)
        reason_codes.append(f"MISSING_FIELDS_{'_'.join(missing_fields).upper()} (+{max(0, 20 - penalty)})")

    # 4. Segment Classification (Max 15 pts)
    is_enterprise = False
    if budget is not None:
        try:
            if float(budget) >= 50000:
                is_enterprise = True
        except ValueError:
            pass
            
    segment = "Enterprise" if is_enterprise else "SMB"
    if is_enterprise:
        score += 15
        reason_codes.append("SEGMENT_ENTERPRISE (+$15)")
    else:
        score += 10
        reason_codes.append("SEGMENT_SMB (+$10)")

    # 5. Timeline specificity (Max 15 pts)
    timeline = str(email_data.get("timeline", "")).lower()
    if timeline and any(k in timeline for k in ["month", "days", "immediate", "now"]):
        score += 15
        reason_codes.append("TIMELINE_SPECIFIED (+$15)")
    else:
        score += 5
        reason_codes.append("TIMELINE_VAGUE (+$5)")

    # 6. Quote Attachment Quality (Max 15 pts)
    if quote_data:
        ocr_conf = quote_data.get("confidence", 0.0)
        if ocr_conf >= 0.90:
            score += 15
            reason_codes.append("OCR_HIGH_CONF (+$15)")
        elif ocr_conf >= 0.70:
            score += 10
            reason_codes.append("OCR_MED_CONF (+$10)")
        else:
            score += 0
            reason_codes.append("OCR_LOW_CONF (+0)")
    else:
        score += 10
        reason_codes.append("NO_ATTACHMENT_DEFAULT (+$10)")

    # Cap score at 100 max
    score = min(100, score)

    # Scoring bands
    if score >= 80:
        classification = "Hot Lead"
        stage = "Proposal Preparation"
        next_action = "Generate Proposal"
    elif score >= 60:
        classification = "Qualified"
        stage = "Needs Discovery"
        next_action = "Schedule Discovery Call"
    elif score >= 40:
        classification = "Needs Clarification"
        stage = "Information Request"
        next_action = "Send Clarification Email"
    else:
        classification = "Nurture"
        stage = "Lead Nurturing"
        next_action = "Add to Email Campaign"

    return {
        "score": score,
        "segment": segment,
        "classification": classification,
        "recommended_pipeline_stage": stage,
        "recommended_next_action": next_action,
        "reason_codes": reason_codes
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Requires JSON input representing email/quote data"}))
        sys.exit(1)
        
    try:
        input_data = json.loads(sys.argv[1])
        email = input_data.get("email_data", input_data)
        quote = input_data.get("quote_data")
        result = calculate_lead_score(email, quote)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
