import os
import csv
import json
import sys

def ingest_all(inventory_path, thresholds_path, supplier_master_path=None):
    """
    Ingests inventory records, merges with threshold limits, validates, and status tags.
    """
    # Read thresholds rules
    thresholds = {}
    if os.path.exists(thresholds_path):
        with open(thresholds_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sku = row["sku"].strip()
                thresholds[sku] = row
                
    # Read supplier master to validate supplier existence
    valid_suppliers = set()
    if supplier_master_path and os.path.exists(supplier_master_path):
        with open(supplier_master_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                valid_suppliers.add(row["supplier_id"].strip())
                
    results = {}
    if not os.path.exists(inventory_path):
        return {"error": f"Inventory file {inventory_path} not found"}

    with open(inventory_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = (row.get("sku") or "").strip()
            if not sku:
                continue
                
            # Default values
            item_name = row.get("item_name") or "Unknown Item"
            category = row.get("category") or "General"
            warehouse = row.get("warehouse") or "WH-Default"
            preferred_supplier = (row.get("preferred_supplier") or "").strip()
            last_restocked = row.get("last_restocked") or ""
            criticality = row.get("criticality") or "MEDIUM"
            
            # Validation Flags
            missing_stock = False
            missing_threshold = False
            invalid_cost = False
            missing_supplier = False
            
            # Parse current stock
            try:
                current_stock = float(row.get("current_stock", ""))
            except (ValueError, TypeError):
                current_stock = 0.0
                missing_stock = True
                
            # Parse average daily usage
            try:
                avg_daily_usage = float(row.get("average_daily_usage", ""))
                if avg_daily_usage < 0:
                    avg_daily_usage = 0.0
            except (ValueError, TypeError):
                avg_daily_usage = 1.0 # fallback default to prevent division by zero
                
            # Parse unit cost
            try:
                unit_cost = float(row.get("unit_cost", ""))
                if unit_cost <= 0:
                    invalid_cost = True
            except (ValueError, TypeError):
                unit_cost = 0.0
                invalid_cost = True
                
            # Supplier check
            if not preferred_supplier:
                missing_supplier = True
            elif valid_suppliers and preferred_supplier not in valid_suppliers:
                missing_supplier = True
                
            # Retrieve threshold values
            threshold_data = thresholds.get(sku)
            if not threshold_data:
                missing_threshold = True
                min_stock = 10.0
                target_stock = 50.0
                urgent_thresh = 5.0
                approval_limit = 5000.0
            else:
                try:
                    min_stock = float(threshold_data.get("minimum_stock", 10.0))
                    target_stock = float(threshold_data.get("target_stock", 50.0))
                    urgent_thresh = float(threshold_data.get("urgent_threshold", 5.0))
                    approval_limit = float(threshold_data.get("approval_required_above_value", 5000.0))
                except (ValueError, TypeError):
                    missing_threshold = True
                    min_stock = 10.0
                    target_stock = 50.0
                    urgent_thresh = 5.0
                    approval_limit = 5000.0

            # Calculate days of stock remaining
            if avg_daily_usage > 0:
                days_remaining = current_stock / avg_daily_usage
            else:
                days_remaining = 365.0 # infinite stock practically
                
            # Status classification
            # Base logic defaults to healthy, then degrades
            status = "HEALTHY"
            
            # Simple threshold triggers
            if current_stock <= urgent_thresh:
                status = "CRITICAL"
            elif current_stock <= min_stock:
                status = "LOW_STOCK"
                
            results[sku] = {
                "sku": sku,
                "item_name": item_name,
                "category": category,
                "warehouse": warehouse,
                "current_stock": current_stock,
                "reorder_threshold": min_stock,
                "target_stock": target_stock,
                "urgent_threshold": urgent_thresh,
                "approval_required_above_value": approval_limit,
                "unit_cost": unit_cost,
                "preferred_supplier": preferred_supplier,
                "last_restocked": last_restocked,
                "average_daily_usage": avg_daily_usage,
                "criticality": criticality,
                "days_remaining": days_remaining,
                "status": status,
                "flags": {
                    "missing_stock": missing_stock,
                    "missing_threshold": missing_threshold,
                    "invalid_cost": invalid_cost,
                    "missing_supplier": missing_supplier
                }
            }
            
    return results

if __name__ == "__main__":
    # Handle direct execution
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inv_file = os.path.join(base_dir, "business_data", "inventory", "current_stock.csv")
    thresh_file = os.path.join(base_dir, "business_data", "inventory", "reorder_thresholds.csv")
    supp_file = os.path.join(base_dir, "business_data", "suppliers", "supplier_master.csv")
    
    if len(sys.argv) > 1:
        inv_file = sys.argv[1]
    if len(sys.argv) > 2:
        thresh_file = sys.argv[2]
        
    out = ingest_all(inv_file, thresh_file, supp_file)
    print(json.dumps(out, indent=2))
