import os
import csv
import json
import sys

def select_supplier(supplier_master_path, category, preferred_supplier_id, urgency, supplier_updates=None):
    """
    Selects the best supplier and backup supplier based on master list and parsed email updates.
    """
    if not os.path.exists(supplier_master_path):
        return {"error": f"Supplier master file {supplier_master_path} not found"}
        
    suppliers = []
    with open(supplier_master_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            suppliers.append(row)
            
    updates = supplier_updates or {}
    
    scored_suppliers = []
    for s in suppliers:
        s_id = s["supplier_id"].strip()
        s_name = s["supplier_name"].strip()
        pref_cats = [c.strip() for c in s.get("preferred_categories", "").split(",")]
        
        # Base scores
        reliability = float(s.get("reliability_score", 0.90))
        lead_time = float(s.get("average_lead_time_days", 7.0))
        
        # Score calculation components
        score = 0.0
        risk_flags = []
        
        # 1. Preferred Supplier matching
        is_preferred = (s_id == preferred_supplier_id)
        if is_preferred:
            score += 50.0
            
        # 2. Category fit
        if category in pref_cats:
            score += 20.0
            
        # 3. Reliability score (0 to 100)
        score += reliability * 100
        
        # 4. Lead time score (lower lead time is better)
        # Assuming lead time up to 20 days. Subtract 3 points per day.
        score += max(0.0, 60.0 - (lead_time * 3.0))
        
        # 5. Process updates (price changes, delays)
        # Check if we have an active update for this supplier
        supplier_update = updates.get(s_id)
        if supplier_update:
            # Check availability status
            if supplier_update.get("availability_status") == "DELAYED":
                score -= 80.0 # large penalty
                risk_flags.append(f"SHIPMENT_DELAY: {supplier_update.get('delay_reason')}")
                lead_time = float(supplier_update.get("updated_lead_time_days", lead_time))
                
            # Check price change percent
            price_change = float(supplier_update.get("price_change_percent", 0.0))
            if price_change > 0.0:
                score -= price_change * 3.0 # penalty proportional to price increase
                risk_flags.append(f"PRICE_INCREASE: +{price_change}%")
                
        scored_suppliers.append({
            "supplier_id": s_id,
            "supplier_name": s_name,
            "contact_name": s["contact_name"].strip(),
            "email": s["email"].strip(),
            "score": score,
            "lead_time": lead_time,
            "reliability": reliability,
            "payment_terms": s["standard_payment_terms"].strip(),
            "risk_flags": risk_flags
        })
        
    # Sort suppliers by score descending
    scored_suppliers.sort(key=lambda x: x["score"], reverse=True)
    
    if len(scored_suppliers) == 0:
        return {"error": "No suppliers available"}
        
    selected = scored_suppliers[0]
    backup = scored_suppliers[1] if len(scored_suppliers) > 1 else None
    
    # Selection reasons formulation
    reason = f"Supplier {selected['supplier_name']} selected based on score of {selected['score']:.1f}. "
    if selected["supplier_id"] == preferred_supplier_id:
        reason += "Matches preferred vendor profile. "
    if selected["risk_flags"]:
        reason += f"Warning: {', '.join(selected['risk_flags'])}. "
        if backup and not backup["risk_flags"]:
            reason += f"Recommended switching to backup: {backup['supplier_name']} due to risk factors."
            
    return {
        "selected_supplier": {
            "supplier_id": selected["supplier_id"],
            "supplier_name": selected["supplier_name"],
            "contact_name": selected["contact_name"],
            "email": selected["email"],
            "payment_terms": selected["payment_terms"],
            "lead_time": selected["lead_time"],
            "score": round(selected["score"], 1)
        },
        "backup_supplier": {
            "supplier_id": backup["supplier_id"] if backup else None,
            "supplier_name": backup["supplier_name"] if backup else None,
            "contact_name": backup["contact_name"] if backup else None,
            "email": backup["email"] if backup else None,
            "score": round(backup["score"], 1) if backup else None
        } if backup else None,
        "supplier_risk_flags": selected["risk_flags"],
        "selection_reason": reason
    }

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    supp_master = os.path.join(base_dir, "business_data", "suppliers", "supplier_master.csv")
    
    # Representative updates subset for test run
    representative_updates = {
        "SUP-003": {
            "supplier_id": "SUP-003",
            "availability_status": "DELAYED",
            "updated_lead_time_days": 18,
            "price_change_percent": 0.0,
            "delay_reason": "supply chain slowdown at component facility"
        }
    }
    
    res = select_supplier(supp_master, "Actuators", "SUP-003", "HIGH", representative_updates)
    print(json.dumps(res, indent=2))
