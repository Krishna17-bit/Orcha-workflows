import os
import sys
import json

def create_followup(sku_data, supplier_data, reason_type, details=None, output_dir=None, templates_dir=None, run_id="LOCAL_RUN"):
    """
    Generates a supplier follow-up notification markdown file.
    """
    sku = sku_data["sku"]
    item_name = sku_data["item_name"]
    selected_sup = supplier_data.get("selected_supplier", {})
    
    supplier_email = selected_sup.get("email", "ops@supplier-link.com")
    supplier_contact = selected_sup.get("contact_name", "Supplier Contact")
    
    # Custom message bodies based on follow-up reason
    bodies = {
        "missing_confirmation": (
            "We have not yet received an order confirmation for our pending procurement request. "
            "Could you please review and confirm whether our target delivery date can be met?"
        ),
        "delay": (
            f"We received your update indicating a shipment delay (estimated lead time: {selected_sup.get('lead_time', 5)} days) "
            "due to component issues. Please let us know if we can expedite this shipment or if there is any "
            "alternative sourcing option available."
        ),
        "price_mismatch": (
            "We noted a billing discrepancy on our recent invoice checklist. The unit price billed "
            f"(${details.get('invoice_price', 0.0):.2f}) is higher than our standard catalog price "
            f"(${sku_data.get('unit_cost', 0.0):.2f}). Please clarify whether this pricing is correct "
            "or if a credit memo should be issued."
        ),
        "more_info": (
            "Our internal compliance check has requested additional documentation before approving "
            "this high-value reorder. Please provide a detailed lead-time assurance statement or "
            "confirm whether any bulk discounts apply to this volume."
        ),
        "urgent": (
            "Due to an active stockout risk, we require immediate dispatch confirmation for this request. "
            "Please confirm if shipping can be expedited and provide tracking details as soon as possible."
        )
    }
    
    followup_body = bodies.get(reason_type, "Please review the status of our pending orders.")
    
    # Load directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not output_dir:
        output_dir = os.path.join(base_dir, "output", "supplier_followups")
    if not templates_dir:
        templates_dir = os.path.join(base_dir, "business_data", "templates")
        
    os.makedirs(output_dir, exist_ok=True)
    
    template_path = os.path.join(templates_dir, "supplier_followup_template.md")
    followup_file_path = os.path.join(output_dir, f"supplier_followup_{sku}.md")
    
    if not os.path.exists(template_path):
        return {"error": f"Template {template_path} not found"}
        
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
        
    content = template.format(
        supplier_email=supplier_email,
        warehouse_manager_email="s.jenkins@orchalabs-ops.com",
        supplier_contact=supplier_contact,
        sku=sku,
        item_name=item_name,
        followup_body=followup_body,
        run_id=run_id
    )
    
    with open(followup_file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    return {
        "status": "SUCCESS",
        "reason_type": reason_type,
        "followup_file": followup_file_path,
        "sku": sku
    }

if __name__ == "__main__":
    example_sku = {"sku": "SKU-004", "item_name": "Copper Fittings", "unit_cost": 8.00}
    example_sup = {
        "selected_supplier": {
            "supplier_id": "SUP-001",
            "supplier_name": "Apex Hardware Group",
            "contact_name": "Robert Chen",
            "email": "r.chen@apexhardware-supply.com"
        }
    }
    details = {"invoice_price": 9.50}
    res = create_followup(example_sku, example_sup, "price_mismatch", details)
    print(json.dumps(res, indent=2))
