import os
import csv
import sys
import json
from datetime import datetime

def update_tracker(tracker_path, po_data):
    """
    Idempotently updates the open purchase orders CSV database.
    """
    if not os.path.exists(tracker_path):
        # Create file with headers if missing
        headers = [
            "po_id", "sku", "item_name", "supplier_name", "warehouse", 
            "quantity", "unit_price", "total_amount", "urgency", 
            "approval_status", "po_status", "expected_delivery_date", 
            "followup_date", "created_at", "last_updated"
        ]
        with open(tracker_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
    # Read existing entries
    rows = []
    headers = []
    with open(tracker_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            headers = [
                "po_id", "sku", "item_name", "supplier_name", "warehouse", 
                "quantity", "unit_price", "total_amount", "urgency", 
                "approval_status", "po_status", "expected_delivery_date", 
                "followup_date", "created_at", "last_updated"
            ]
        for row in reader:
            if row:
                rows.append(row)
                
    po_id = po_data.get("po_id", "")
    sku = po_data.get("sku", "")
    supplier_name = po_data.get("supplier_name", "")
    created_at = po_data.get("created_at", datetime.now().strftime("%Y-%m-%d"))
    
    # Check for duplicates using po_id or sku + supplier + created_at
    match_index = -1
    for idx, r in enumerate(rows):
        # Map fields by header index
        r_po_id = r[headers.index("po_id")] if "po_id" in headers else ""
        r_sku = r[headers.index("sku")] if "sku" in headers else ""
        r_supplier = r[headers.index("supplier_name")] if "supplier_name" in headers else ""
        r_created = r[headers.index("created_at")] if "created_at" in headers else ""
        
        if po_id and r_po_id == po_id:
            match_index = idx
            break
        elif not po_id and r_sku == sku and r_supplier == supplier_name and r_created == created_at:
            match_index = idx
            break
            
    # Prepare row data
    row_dict = {h: "" for h in headers}
    row_dict["po_id"] = po_id
    row_dict["sku"] = sku
    row_dict["item_name"] = po_data.get("item_name", "")
    row_dict["supplier_name"] = supplier_name
    row_dict["warehouse"] = po_data.get("warehouse", "")
    row_dict["quantity"] = str(po_data.get("quantity", ""))
    row_dict["unit_price"] = f"{float(po_data.get('unit_price', 0.0)):.2f}"
    row_dict["total_amount"] = f"{float(po_data.get('total_amount', 0.0)):.2f}"
    row_dict["urgency"] = po_data.get("urgency", "STANDARD")
    row_dict["approval_status"] = po_data.get("approval_status", "APPROVED")
    row_dict["po_status"] = po_data.get("po_status", "OPEN")
    row_dict["expected_delivery_date"] = po_data.get("expected_delivery_date", "")
    row_dict["followup_date"] = po_data.get("followup_date", "")
    row_dict["created_at"] = created_at
    row_dict["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    
    new_row = [row_dict[h] for h in headers]
    
    if match_index >= 0:
        # Update existing
        # Preserve original po_id or created_at if missing
        if not new_row[headers.index("po_id")] and rows[match_index][headers.index("po_id")]:
            new_row[headers.index("po_id")] = rows[match_index][headers.index("po_id")]
        rows[match_index] = new_row
        action = "UPDATE"
    else:
        # Append new
        rows.append(new_row)
        action = "INSERT"
        
    # Write back to CSV
    with open(tracker_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)
        
    return {
        "status": "SUCCESS",
        "action": action,
        "po_id": new_row[headers.index("po_id")],
        "sku": sku
    }

if __name__ == "__main__":
    # Test tracking update
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tracker = os.path.join(base_dir, "business_data", "procurement", "open_purchase_orders.csv")
    
    test_data = {
        "po_id": "PO-2026-TEST-9999",
        "sku": "SKU-999",
        "item_name": "Test Widgets",
        "supplier_name": "Apex Hardware Group",
        "warehouse": "WH-001",
        "quantity": 100,
        "unit_price": 1.50,
        "total_amount": 150.00,
        "urgency": "STANDARD",
        "approval_status": "APPROVED",
        "po_status": "OPEN",
        "expected_delivery_date": "2026-07-15",
        "followup_date": "2026-07-16",
        "created_at": "2026-07-09"
    }
    
    res = update_tracker(tracker, test_data)
    print(json.dumps(res, indent=2))
