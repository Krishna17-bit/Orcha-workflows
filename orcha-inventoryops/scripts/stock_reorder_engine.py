import os
import sys
import json
from datetime import datetime, timedelta

def evaluate_reorder(sku_data, lead_time_days=5):
    """
    Evaluates a single SKU data dict and determines procurement necessity.
    """
    current_stock = sku_data.get("current_stock", 0.0)
    reorder_threshold = sku_data.get("reorder_threshold", 10.0)
    target_stock = sku_data.get("target_stock", 50.0)
    urgent_threshold = sku_data.get("urgent_threshold", 5.0)
    average_daily_usage = sku_data.get("average_daily_usage", 1.0)
    criticality = sku_data.get("criticality", "MEDIUM")
    
    reorder_needed = False
    recommended_quantity = 0.0
    urgency_level = "STANDARD"
    reason_codes = []
    recommended_action = "MONITOR"
    
    # Calculate days of stock remaining
    if average_daily_usage > 0:
        days_remaining = current_stock / average_daily_usage
    else:
        days_remaining = 365.0
        
    estimated_stockout_date = (datetime.now() + timedelta(days=days_remaining)).strftime("%Y-%m-%d")
    
    # Check trigger rules
    if current_stock <= reorder_threshold:
        reorder_needed = True
        recommended_quantity = target_stock - current_stock
        reason_codes.append("BELOW_REORDER_THRESHOLD")
        urgency_level = "STANDARD"
        recommended_action = "PLACE_REORDER"
        
        # Elevate to HIGH if usage is high or criticality is high
        if criticality in ["HIGH", "CRITICAL"] or days_remaining <= lead_time_days:
            urgency_level = "HIGH"
            
    if current_stock <= urgent_threshold:
        reorder_needed = True
        recommended_quantity = target_stock - current_stock
        reason_codes.append("BELOW_URGENT_THRESHOLD")
        urgency_level = "CRITICAL"
        recommended_action = "EXPEDITE_REORDER"
        
    if days_remaining < lead_time_days and current_stock > 0:
        reorder_needed = True
        # If not already reordering, compute recommended quantity
        if recommended_quantity == 0:
            recommended_quantity = target_stock - current_stock
        reason_codes.append("STOCKOUT_RISK_LEAD_TIME")
        urgency_level = "CRITICAL"
        recommended_action = "EXPEDITE_REORDER"
        
    if current_stock == 0:
        reorder_needed = True
        recommended_quantity = target_stock
        reason_codes.append("STOCKOUT_ACTIVE")
        urgency_level = "CRITICAL"
        recommended_action = "EMERGENCY_REORDER"

    if not reorder_needed:
        reason_codes.append("HEALTHY_STOCK")
        
    return {
        "sku": sku_data["sku"],
        "item_name": sku_data["item_name"],
        "reorder_needed": reorder_needed,
        "recommended_quantity": max(0.0, recommended_quantity),
        "urgency_level": urgency_level,
        "reason_codes": reason_codes,
        "days_remaining": days_remaining,
        "estimated_stockout_date": estimated_stockout_date,
        "recommended_action": recommended_action
    }

if __name__ == "__main__":
    # Test wrapper
    if len(sys.argv) > 1:
        sku_json = sys.argv[1]
        try:
            data = json.loads(sku_json)
            print(json.dumps(evaluate_reorder(data), indent=2))
        except Exception as e:
            print(json.dumps({"error": f"Failed to parse input SKU JSON: {e}"}))
    else:
        # Example SKU data evaluation
        example_sku = {
            "sku": "SKU-003",
            "item_name": "Hydraulic Valves",
            "current_stock": 5.0,
            "reorder_threshold": 30.0,
            "target_stock": 80.0,
            "urgent_threshold": 6.0,
            "average_daily_usage": 4.0,
            "criticality": "CRITICAL"
        }
        print(json.dumps(evaluate_reorder(example_sku, lead_time_days=7), indent=2))
