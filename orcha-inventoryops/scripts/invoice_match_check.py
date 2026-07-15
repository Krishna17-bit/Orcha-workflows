import os
import csv
import json
import sys

def check_invoice_match(invoice_data, expected_unit_cost, standard_payment_terms=None, expected_qty=None, rules_path=None):
    """
    Checks invoice parameters against internal inventory expectations and matching rules.
    """
    sku = invoice_data.get("sku")
    inv_unit_price = invoice_data.get("unit_price")
    inv_qty = invoice_data.get("quantity")
    inv_total = invoice_data.get("total_amount")
    inv_terms = invoice_data.get("payment_terms")
    
    # Load rules
    rules = {}
    if rules_path and os.path.exists(rules_path):
        with open(rules_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rules[row["field"]] = {
                    "tolerance": float(row["tolerance"]),
                    "action": row["action"]
                }
                
    # Tolerances defaults
    price_tol = rules.get("unit_price", {}).get("tolerance", 0.02)
    qty_tol = rules.get("quantity", {}).get("tolerance", 0.00)
    total_tol = rules.get("total_amount", {}).get("tolerance", 0.01)
    
    mismatch_reasons = []
    match_status = "MATCHED"
    approval_required = False
    recommended_resolution = "PROCEED_TO_PAYMENT"
    
    # 1. Missing basic fields check
    if not invoice_data.get("invoice_id") or not sku or inv_unit_price is None or inv_qty is None or inv_total is None:
        mismatch_reasons.append("MISSING_INVOICE_FIELDS")
        match_status = "REVIEW_REQUIRED"
        approval_required = True
        recommended_resolution = "ROUTE_TO_MANUAL_OCR_REVIEW"
        return {
            "match_status": match_status,
            "mismatch_reasons": mismatch_reasons,
            "approval_required": approval_required,
            "recommended_resolution": recommended_resolution
        }

    # 2. Check Unit Price Mismatch
    # If invoice price is different from stock catalog price
    price_diff_percent = abs(inv_unit_price - expected_unit_cost) / expected_unit_cost
    if price_diff_percent > price_tol:
        mismatch_reasons.append(f"UNIT_PRICE_MISMATCH: Invoice ${inv_unit_price:.2f} vs Expected ${expected_unit_cost:.2f} (Diff: {price_diff_percent*100:.1f}%, Tolerance: {price_tol*100:.1f}%)")
        match_status = "MISMATCH"
        approval_required = True
        recommended_resolution = "ROUTE_TO_FINANCE_DIRECTOR_FOR_PRICING_VARIANCE"

    # 3. Check Quantity Mismatch if expected qty is provided
    if expected_qty is not None:
        qty_diff = abs(inv_qty - expected_qty)
        if qty_diff > qty_tol:
            mismatch_reasons.append(f"QUANTITY_MISMATCH: Invoice qty {inv_qty} vs Expected qty {expected_qty}")
            match_status = "MISMATCH"
            approval_required = True
            recommended_resolution = "HOLD_INVOICE_AND_CONTACT_SUPPLIER_FOR_SHIPPING_CORRECTION"

    # 4. Check Total Amount Math Mismatch
    expected_total = inv_qty * inv_unit_price
    total_diff_percent = abs(inv_total - expected_total) / expected_total if expected_total > 0 else 0
    if total_diff_percent > total_tol:
        mismatch_reasons.append(f"TOTAL_AMOUNT_MATH_MISMATCH: Invoice Total ${inv_total:.2f} vs Expected Math ${expected_total:.2f}")
        match_status = "MISMATCH"
        approval_required = True
        recommended_resolution = "HOLD_INVOICE_FOR_BILLING_MATH_CHECK"

    # 5. Check Non-Standard Payment Terms
    if standard_payment_terms and inv_terms:
        if inv_terms.strip() != standard_payment_terms.strip():
            mismatch_reasons.append(f"PAYMENT_TERMS_VARIANCE: Invoice {inv_terms} vs Standard {standard_payment_terms}")
            if match_status == "MATCHED":
                match_status = "REVIEW_REQUIRED"
                approval_required = True
                recommended_resolution = "ROUTE_TO_PROCUREMENT_LEAD_FOR_TERMS_REVIEW"

    # 6. Check Urgent delivery surcharges (e.g. total is higher than unit * qty, or flag exists)
    if "urgent" in str(invoice_data).lower() and inv_total > expected_total:
        mismatch_reasons.append("URGENT_DELIVERY_SURCHARGE_APPLIED")
        match_status = "REVIEW_REQUIRED"
        approval_required = True
        recommended_resolution = "ROUTE_TO_OPS_MANAGER_FOR_EXPEDITED_FEE_APPROVAL"

    return {
        "match_status": match_status,
        "mismatch_reasons": mismatch_reasons,
        "approval_required": approval_required,
        "recommended_resolution": recommended_resolution
    }

if __name__ == "__main__":
    # Representative invoice matching scenario
    representative_invoice = {
        "invoice_id": "INV-2026-8803",
        "supplier_name": "Apex Hardware Group",
        "sku": "SKU-004",
        "quantity": 130,
        "unit_price": 9.50,
        "total_amount": 1235.00,
        "payment_terms": "Net 30"
    }
    
    res = check_invoice_match(representative_invoice, expected_unit_cost=8.00, standard_payment_terms="Net 30")
    print(json.dumps(res, indent=2))
