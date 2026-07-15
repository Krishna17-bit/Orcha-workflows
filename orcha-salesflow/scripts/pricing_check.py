import os
import re
import csv
import sys
import json

def load_csv_data(file_path):
    rows = []
    if not os.path.exists(file_path):
        return rows
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def check_pricing(email_data, quote_data=None):
    # Resolve file paths relative to script location
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    rules_path = os.path.join(base_dir, "business_data/crm/pricing_rules.csv")
    catalog_path = os.path.join(base_dir, "business_data/crm/product_catalog.csv")
    
    rules = load_csv_data(rules_path)
    catalog = load_csv_data(catalog_path)

    # 1. Resolve requested service to catalog
    req_service = email_data.get("requirement") or ""
    if quote_data and quote_data.get("requested_service"):
        req_service = quote_data.get("requested_service")
        
    product = None
    for p in catalog:
        # Match using substring case-insensitive
        if p["product_name"].lower() in req_service.lower() or req_service.lower() in p["product_name"].lower():
            product = p
            break
            
    base_price = 0.0
    min_budget = 0.0
    service_name = req_service
    is_monthly = False
    
    if product:
        service_name = product["product_name"]
        base_price = float(product["base_price"])
        min_budget = float(product["min_budget"])
        if product["price_unit"] == "monthly":
            is_monthly = True
            timeline_str = email_data.get("timeline") or ""
            months = 1
            months_match = re.search(r"(\d+)\s*month", str(timeline_str), re.IGNORECASE)
            if months_match:
                months = int(months_match.group(1))
            base_price = base_price * months
            min_budget = min_budget * months

    # 2. Extract values from lead/quote
    budget = email_data.get("budget")
    if quote_data and quote_data.get("estimated_budget") is not None:
        budget = quote_data.get("estimated_budget")
        
    requested_discount = 0.0
    if quote_data and quote_data.get("requested_discount") is not None:
        requested_discount = float(quote_data["requested_discount"])
        
    payment_terms = "Net 30"
    if quote_data and quote_data.get("payment_terms"):
        payment_terms = quote_data["payment_terms"]
    elif email_data.get("payment_terms"):
        payment_terms = email_data["payment_terms"]

    urgency = email_data.get("urgency") or ""
    
    # 3. Run evaluations against policy catalog
    approval_required = False
    approval_reasons = []
    
    # Urgent delivery surcharge premium (10%)
    surcharge = 0.0
    is_urgent = any(k in str(urgency).lower() for k in ["critical", "immediate", "urgent", "high"])
    if is_urgent:
        surcharge = base_price * 0.10
        
    # Discount limit check
    max_discount = 0.15
    for r in rules:
        if r["rule_id"] == "PR_001":
            max_discount = float(r["value"])
            
    if requested_discount > max_discount:
        approval_required = True
        approval_reasons.append(f"Requested discount of {requested_discount*100:.1f}% exceeds standard limit of {max_discount*100:.1f}%.")

    # Min deal value budget threshold check
    if budget is not None:
        try:
            budget_val = float(budget)
            if budget_val < min_budget:
                approval_required = True
                approval_reasons.append(f"Budget of ${budget_val:,.2f} is below the minimum required standard for {service_name} (${min_budget:,.2f}).")
        except ValueError:
            pass

    # Payment terms standard verification
    standard_terms = ["Net 30", "net 30", "Net30", "net30"]
    non_std_terms = ["Net 60", "Net 90", "net 60", "net 90", "Net60", "Net90"]
    is_non_standard_term = any(t in payment_terms for t in non_std_terms)
    if is_non_standard_term or (payment_terms not in standard_terms and payment_terms != "Net 30"):
        approval_required = True
        approval_reasons.append(f"Requested payment terms '{payment_terms}' are non-standard. Standard is Net 30.")

    # Calculate final financials
    proposed_deal_value = (base_price + surcharge) * (1 - requested_discount)
    if budget is not None:
        try:
            proposed_deal_value = float(budget)
        except ValueError:
            pass

    # Suggested standard pricing based on max discount rule
    suggested_price = (base_price + surcharge) * (1 - min(requested_discount, max_discount))

    return {
        "approval_required": approval_required,
        "approval_reasons": approval_reasons,
        "service_name": service_name,
        "base_price": base_price,
        "surcharge": surcharge,
        "proposed_deal_value": proposed_deal_value,
        "suggested_price": suggested_price,
        "requested_discount_pct": requested_discount * 100.0,
        "max_allowed_discount_pct": max_discount * 100.0,
        "payment_terms": payment_terms,
        "final_decision_pending": approval_required
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Requires JSON input representing email/quote data"}))
        sys.exit(1)
        
    try:
        input_data = json.loads(sys.argv[1])
        email = input_data.get("email_data", input_data)
        quote = input_data.get("quote_data")
        result = check_pricing(email, quote)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
