import os
import sys
import json

def route_approval(sku_data, reorder_data, supplier_data, match_data=None, approvals_dir=None, templates_dir=None, run_id="LOCAL_RUN"):
    """
    Checks if a procurement request requires approval, writes requests, and checks for manual decisions.
    """
    sku = sku_data.get("sku")
    unit_cost = sku_data.get("unit_cost", 0.0)
    qty = reorder_data.get("recommended_quantity", 0.0)
    total_value = qty * unit_cost
    approval_limit = sku_data.get("approval_required_above_value", 5000.0)
    urgency = reorder_data.get("urgency_level", "STANDARD")
    reliability = supplier_data.get("selected_supplier", {}).get("reliability", 1.0)
    
    reasons = []
    
    # 1. Total purchase value exceeds threshold
    if total_value > approval_limit:
        reasons.append(f"HIGH_VALUE_THRESHOLD: Purchase value ${total_value:,.2f} exceeds threshold limit of ${approval_limit:,.2f}")
        
    # 2. Critical stockout risk urgency check
    if urgency == "CRITICAL" and total_value > 1000.0:
        reasons.append(f"URGENT_CRITICAL_STOCKOUT: Urgency is CRITICAL and value ${total_value:,.2f} is above safety boundary $1,000.00")
        
    # 3. Invoice price mismatch check
    if match_data and match_data.get("match_status") == "MISMATCH":
        reasons.append(f"INVOICE_PRICING_MISMATCH: Invoice matching flagged mismatch reasons: {', '.join(match_data.get('mismatch_reasons', []))}")
        
    # 4. Low supplier reliability
    if reliability < 0.90:
        reasons.append(f"LOW_RELIABILITY_VENDOR: Supplier reliability {reliability} is below standard compliance score 0.90")
        
    # 5. Non-standard terms or manual reviews from matching
    if match_data and match_data.get("match_status") == "REVIEW_REQUIRED":
        reasons.append(f"POLICY_COMPLIANCE_REVIEW: Invoice matching requires compliance review: {', '.join(match_data.get('mismatch_reasons', []))}")

    approval_required = len(reasons) > 0
    
    if not approval_required:
        return {
            "approval_required": False,
            "decision": "APPROVED",
            "approver_role": "SYSTEM_AUTO",
            "routing_reasons": []
        }
        
    # Determine appropriate approver
    approver_role = "Operations Manager"
    for r in reasons:
        if "HIGH_VALUE" in r:
            approver_role = "VP of Operations"
        elif "PRICING_MISMATCH" in r:
            approver_role = "Finance Director"
        elif "LOW_RELIABILITY" in r:
            approver_role = "Procurement Lead"
            
    # Setup directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not approvals_dir:
        approvals_dir = os.path.join(base_dir, "output", "approvals")
    if not templates_dir:
        templates_dir = os.path.join(base_dir, "business_data", "templates")
        
    os.makedirs(approvals_dir, exist_ok=True)
    
    # Generate approval request Markdown file
    req_file_path = os.path.join(approvals_dir, f"approval_request_{sku}.md")
    template_path = os.path.join(templates_dir, "approval_request_template.md")
    
    # Write approval request using template
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            template = f.read()
            
        routing_reasons_str = "\n".join([f"- {r}" for r in reasons])
        proposed_dec = "APPROVE"
        if "PRICING_MISMATCH" in str(reasons):
            proposed_dec = "REQUEST_MORE_INFO"
        elif "LOW_RELIABILITY" in str(reasons):
            proposed_dec = "REJECT"
            
        rec_text = "Recommend approving the purchase to prevent supply chain disruption."
        if proposed_dec == "REQUEST_MORE_INFO":
            rec_text = "Recommend contacting supplier to verify billing discrepancy."
        elif proposed_dec == "REJECT":
            rec_text = "Recommend routing to backup supplier."
            
        req_content = template.format(
            sku=sku,
            item_name=sku_data.get("item_name", "Unknown"),
            category=sku_data.get("category", "General"),
            warehouse=sku_data.get("warehouse", "WH-001"),
            supplier_name=supplier_data.get("selected_supplier", {}).get("supplier_name", "Unknown Supplier"),
            quantity=qty,
            unit_cost=unit_cost,
            total_value=total_value,
            routing_reasons=routing_reasons_str,
            urgency=urgency,
            proposed_decision=proposed_dec,
            recommendation_text=rec_text,
            run_id=run_id
        )
        
        with open(req_file_path, "w", encoding="utf-8") as f:
            f.write(req_content)
            
    # Check for approval decision file
    decision_file_path = os.path.join(approvals_dir, f"approval_decision_{sku}.txt")
    
    if os.path.exists(decision_file_path):
        with open(decision_file_path, "r", encoding="utf-8") as f:
            decision = f.read().strip().upper()
        # Clean any comments or headers
        lines = [line.strip() for line in decision.split("\n") if line.strip() and not line.strip().startswith("#")]
        if lines:
            decision = lines[0]
        else:
            decision = "PENDING"
    else:
        # Create an empty template decision file to let the user review it
        with open(decision_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Decision file for SKU {sku}\n")
            f.write("# Enter exactly one of: APPROVE, REJECT, REQUEST_MORE_INFO\n")
            f.write("PENDING\n")
        decision = "PENDING"
        
    return {
        "approval_required": True,
        "decision": decision,
        "approver_role": approver_role,
        "routing_reasons": reasons,
        "decision_file": decision_file_path,
        "request_file": req_file_path
    }

if __name__ == "__main__":
    # Test router
    example_sku = {"sku": "SKU-006", "unit_cost": 3500.0, "item_name": "Turbine Rotors", "approval_required_above_value": 10000.0}
    example_reorder = {"recommended_quantity": 8, "urgency_level": "CRITICAL"}
    example_supplier = {"selected_supplier": {"supplier_name": "Heavy Rotation Systems", "reliability": 0.97}}
    
    res = route_approval(example_sku, example_reorder, example_supplier)
    print(json.dumps(res, indent=2))
