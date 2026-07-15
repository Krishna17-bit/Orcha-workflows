import os
import csv
import sys
import json
from datetime import datetime, timedelta

def update_crm_pipeline(lead_data, score_data, pricing_data, proposal_path=None, output_dir_base=None):
    if not output_dir_base:
        output_dir_base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
    crm_path = os.path.join(output_dir_base, "business_data/crm/sales_pipeline.csv")
    
    lead_id = lead_data.get("lead_id", "UNKNOWN")
    company_name = lead_data.get("company_name", "Unknown Co")
    contact_name = lead_data.get("contact_name", "Unknown Contact")
    email = lead_data.get("email", "unknown@client.com")
    
    score = score_data.get("score", 0)
    stage = score_data.get("recommended_pipeline_stage", "Needs Discovery")
    next_action = score_data.get("recommended_next_action", "Schedule Discovery Call")
    
    deal_value = pricing_data.get("proposed_deal_value", 0.0)
    
    # Resolve approval status and map pipeline stage transitions
    approval_status = "Approved (Standard)"
    if pricing_data.get("approval_required"):
        approval_status = "Pending Approval"
    if pricing_data.get("approved_by_human"):
        approval_status = "Approved (Exception)"
    elif pricing_data.get("rejected_by_human"):
        approval_status = "Rejected"
        stage = "Closed Lost"
        next_action = "Nurture Campaign"
        
    # Calculate scheduling dates: urgent leads are scheduled sooner (2 days vs 7 days)
    urgency = str(lead_data.get("urgency", "")).lower()
    days_to_followup = 7
    if any(k in urgency for k in ["high", "critical", "urgent", "immediate"]):
        days_to_followup = 2
        
    now = datetime.now()
    followup_date = (now + timedelta(days=days_to_followup)).strftime("%Y-%m-%d")
    last_updated = now.strftime("%Y-%m-%d %H:%M:%S")

    # Define CRM Headers
    headers = [
        "lead_id", "company_name", "contact_name", "email", "score", 
        "stage", "deal_value", "approval_status", "next_action", 
        "followup_date", "proposal_path", "last_updated"
    ]
    
    rows = []
    updated = False
    
    if os.path.exists(crm_path):
        with open(crm_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            # Read and filter fields
            for row in reader:
                if row.get("lead_id") == lead_id:
                    # Update existing record
                    row["company_name"] = company_name
                    row["contact_name"] = contact_name
                    row["email"] = email
                    row["score"] = str(score)
                    row["stage"] = stage
                    row["deal_value"] = f"{deal_value:.2f}"
                    row["approval_status"] = approval_status
                    row["next_action"] = next_action
                    row["followup_date"] = followup_date
                    row["proposal_path"] = proposal_path or row.get("proposal_path") or ""
                    row["last_updated"] = last_updated
                    updated = True
                rows.append(row)

    if not updated:
        # Create new CRM record row
        new_row = {
            "lead_id": lead_id,
            "company_name": company_name,
            "contact_name": contact_name,
            "email": email,
            "score": str(score),
            "stage": stage,
            "deal_value": f"{deal_value:.2f}",
            "approval_status": approval_status,
            "next_action": next_action,
            "followup_date": followup_date,
            "proposal_path": proposal_path or "",
            "last_updated": last_updated
        }
        rows.append(new_row)

    # Idempotent write to local CSV CRM
    with open(crm_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    return {
        "status": "success",
        "lead_id": lead_id,
        "stage": stage,
        "deal_value": deal_value,
        "followup_date": followup_date
    }

if __name__ == "__main__":
    # Standard terminal node invocation printout
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Requires JSON input representing lead & scoring & pricing details"}))
        sys.exit(1)
        
    try:
        input_data = json.loads(sys.argv[1])
        lead = input_data.get("lead_data", {})
        score = input_data.get("score_data", {})
        pricing = input_data.get("pricing_data", {})
        prop_path = input_data.get("proposal_path")
        result = update_crm_pipeline(lead, score, pricing, prop_path)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
