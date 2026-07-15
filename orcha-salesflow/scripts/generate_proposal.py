import os
import sys
import json
from datetime import datetime

def generate_documents(lead_data, pricing_data, output_dir_base=None):
    if not output_dir_base:
        output_dir_base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
    templates_dir = os.path.join(output_dir_base, "business_data/templates")
    proposals_dir = os.path.join(output_dir_base, "output/proposals")
    approvals_dir = os.path.join(output_dir_base, "output/approvals")
    
    os.makedirs(proposals_dir, exist_ok=True)
    os.makedirs(approvals_dir, exist_ok=True)

    lead_id = lead_data.get("lead_id", "UNKNOWN")
    company_name = lead_data.get("company_name", "Valued Client")
    service_name = pricing_data.get("service_name") or lead_data.get("requirement") or "B2B Services"
    
    current_date = datetime.now().strftime("%B %d, %Y")

    # Dynamic generation of executive summary for B2B proposal
    urgency = lead_data.get("urgency", "Standard")
    timeline = lead_data.get("timeline", "To be agreed")
    
    exec_summary = f"This proposal has been custom-compiled in response to {company_name}'s request for {service_name}. "
    if "high" in str(urgency).lower() or "critical" in str(urgency).lower():
        exec_summary += f"Due to the high urgency and rapid implementation schedule ({timeline}), we have structured a dedicated delivery path to meet your objectives."
    else:
        exec_summary += f"We have structured our deliverables over a {timeline} horizon to ensure thorough alignment, quality, and complete verification."

    # 1. Process Proposal Markdown
    prop_template_path = os.path.join(templates_dir, "proposal_template.md")
    if not os.path.exists(prop_template_path):
        return {"error": f"Proposal template not found at {prop_template_path}"}
        
    with open(prop_template_path, "r", encoding="utf-8") as f:
        prop_template = f.read()

    app_status = "Approved (Standard Pricing)"
    if pricing_data.get("approval_required"):
        app_status = "Pending Senior Management Approval"
    if pricing_data.get("approved_by_human"):
        app_status = "Approved (Special Exception Authorized)"
    elif pricing_data.get("rejected_by_human"):
        app_status = "Rejected (Pricing Exception Declined)"

    prop_content = prop_template
    replacements = {
        "{{company_name}}": company_name,
        "{{service_name}}": service_name,
        "{{current_date}}": current_date,
        "{{lead_id}}": lead_id,
        "{{executive_summary}}": exec_summary,
        "{{timeline}}": timeline,
        "{{base_price}}": f"{pricing_data.get('base_price', 0.0):,.2f}",
        "{{surcharge}}": f"{pricing_data.get('surcharge', 0.0):,.2f}",
        "{{discount_percentage}}": f"{pricing_data.get('requested_discount_pct', 0.0):.1f}",
        "{{deal_value}}": f"{pricing_data.get('proposed_deal_value', 0.0):,.2f}",
        "{{payment_terms}}": pricing_data.get("payment_terms", "Net 30"),
        "{{approval_status}}": app_status
    }

    for placeholder, val in replacements.items():
        prop_content = prop_content.replace(placeholder, str(val))

    proposal_path = os.path.join(proposals_dir, f"proposal_{lead_id}.md")
    with open(proposal_path, "w", encoding="utf-8") as f:
        f.write(prop_content)

    # 2. Process Approval Request Markdown if pricing exception flagged
    approval_path = None
    if pricing_data.get("approval_required") and not pricing_data.get("approved_by_human") and not pricing_data.get("rejected_by_human"):
        app_template_path = os.path.join(templates_dir, "approval_request_template.md")
        if os.path.exists(app_template_path):
            with open(app_template_path, "r", encoding="utf-8") as f:
                app_template = f.read()

            reasons = pricing_data.get("approval_reasons", [])
            risk_flags = "\n".join([f"- [WARNING] {r}" for r in reasons])
            
            discount_val = pricing_data.get("requested_discount_pct", 0.0)
            max_disc = pricing_data.get("max_allowed_discount_pct", 15.0)
            
            rec_action = "Approve with standard urgency surcharge, or renegotiate discount back to the 15% threshold."
            if discount_val > 20.0:
                rec_action = "Request reduction of discount to 15% standard limit, or apply Net 30 payment terms as counter-offer."

            app_content = app_template
            app_replacements = {
                "{{lead_id}}": lead_id,
                "{{company_name}}": company_name,
                "{{contact_name}}": lead_data.get("contact_name") or "Procurement Officer",
                "{{email}}": lead_data.get("email") or "procurement@client.com",
                "{{urgency}}": urgency,
                "{{risk_flags}}": risk_flags,
                "{{service_name}}": service_name,
                "{{base_price}}": f"{pricing_data.get('base_price', 0.0):,.2f}",
                "{{surcharge}}": f"{pricing_data.get('surcharge', 0.0):,.2f}",
                "{{requested_discount}}": f"{discount_val:.1f}",
                "{{max_allowed_discount}}": f"{max_disc:.1f}",
                "{{proposed_deal_value}}": f"{pricing_data.get('proposed_deal_value', 0.0):,.2f}",
                "{{payment_terms}}": pricing_data.get("payment_terms", "Net 30"),
                "{{recommended_action}}": rec_action
            }

            for placeholder, val in app_replacements.items():
                app_content = app_content.replace(placeholder, str(val))

            approval_path = os.path.join(approvals_dir, f"approval_request_{lead_id}.md")
            with open(approval_path, "w", encoding="utf-8") as f:
                f.write(app_content)

    return {
        "status": "success",
        "proposal_path": proposal_path,
        "approval_path": approval_path,
        "approval_status": app_status
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Requires JSON input representing lead & pricing details"}))
        sys.exit(1)
        
    try:
        input_data = json.loads(sys.argv[1])
        lead = input_data.get("lead_data", {})
        pricing = input_data.get("pricing_data", {})
        result = generate_documents(lead, pricing)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
