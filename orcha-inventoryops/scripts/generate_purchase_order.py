import os
import sys
import json
from datetime import datetime, timedelta

def create_po(sku_data, reorder_data, supplier_data, approval_data, output_dir=None, templates_dir=None, audit_id="SYSTEM"):
    """
    Generates a markdown purchase order from the standard template.
    """
    sku = sku_data["sku"]
    qty = reorder_data["recommended_quantity"]
    unit_price = sku_data["unit_cost"]
    
    # If the supplier update changed the price, use it
    selected_sup = supplier_data.get("selected_supplier", {})
    supplier_id = selected_sup.get("supplier_id")
    supplier_name = selected_sup.get("supplier_name", "Unknown Supplier")
    
    total_amount = qty * unit_price
    
    # Calculate expected delivery date based on lead time
    lead_time = selected_sup.get("lead_time", 5)
    expected_delivery_date = (datetime.now() + timedelta(days=lead_time)).strftime("%Y-%m-%d")
    
    # Generate unique PO number
    timestamp = datetime.now().strftime("%Y%m%d%H%M")
    po_id = f"PO-2026-{sku}-{timestamp}"
    
    # Load directories
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not output_dir:
        output_dir = os.path.join(base_dir, "output", "purchase_orders")
    if not templates_dir:
        templates_dir = os.path.join(base_dir, "business_data", "templates")
        
    os.makedirs(output_dir, exist_ok=True)
    
    template_path = os.path.join(templates_dir, "purchase_order_template.md")
    po_file_path = os.path.join(output_dir, f"purchase_order_{sku}.md")
    
    if not os.path.exists(template_path):
        return {"error": f"Template {template_path} not found"}
        
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
        
    operational_notes = "Standard shipment rules apply."
    if reorder_data.get("urgency_level") == "CRITICAL":
        operational_notes = "CRITICAL STOCKOUT RISK: Requesting expedited dispatch. Please contact the warehouse manager immediately upon shipment."
        
    # Read approval values
    app_required = "YES" if approval_data.get("approval_required") else "NO"
    app_status = approval_data.get("decision", "APPROVED")
    approver = approval_data.get("approver_role", "SYSTEM_AUTO")
    
    po_content = template.format(
        po_id=po_id,
        created_at=datetime.now().strftime("%Y-%m-%d"),
        po_status="OPEN",
        urgency=reorder_data.get("urgency_level", "STANDARD"),
        supplier_id=supplier_id,
        supplier_name=supplier_name,
        supplier_contact=selected_sup.get("contact_name", ""),
        supplier_email=selected_sup.get("email", ""),
        warehouse_id=sku_data.get("warehouse", "WH-001"),
        warehouse_name="Orcha Distribution Center",
        warehouse_city="Local Terminal Depot",
        warehouse_manager="Sarah Jenkins",
        warehouse_manager_email="s.jenkins@orchalabs-ops.com",
        expected_delivery_date=expected_delivery_date,
        sku=sku,
        item_name=sku_data["item_name"],
        quantity=qty,
        unit_price=unit_price,
        total_amount=total_amount,
        payment_terms=selected_sup.get("payment_terms", "Net 30"),
        approval_required=app_required,
        approval_status=app_status,
        approver_role=approver,
        audit_id=audit_id,
        operational_notes=operational_notes
    )
    
    with open(po_file_path, "w", encoding="utf-8") as f:
        f.write(po_content)
        
    return {
        "po_id": po_id,
        "po_file_path": po_file_path,
        "total_amount": total_amount,
        "expected_delivery_date": expected_delivery_date,
        "po_status": "OPEN",
        "approval_status": app_status
    }

if __name__ == "__main__":
    # Test generator
    example_sku = {"sku": "SKU-002", "item_name": "Industrial Gaskets", "unit_cost": 5.0, "warehouse": "WH-001"}
    example_reorder = {"recommended_quantity": 75, "urgency_level": "STANDARD"}
    example_supplier = {
        "selected_supplier": {
            "supplier_id": "SUP-001",
            "supplier_name": "Apex Hardware Group",
            "contact_name": "Robert Chen",
            "email": "r.chen@apexhardware-supply.com",
            "payment_terms": "Net 30",
            "lead_time": 5
        }
    }
    example_approval = {"approval_required": False, "decision": "APPROVED", "approver_role": "SYSTEM_AUTO"}
    
    res = create_po(example_sku, example_reorder, example_supplier, example_approval)
    print(json.dumps(res, indent=2))
