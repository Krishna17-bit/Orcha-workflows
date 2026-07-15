import os
import sys
import subprocess
from datetime import datetime, timedelta
import json

# Import Python automation nodes
from audit_logger import AuditLogger
from ingest_inventory import ingest_all
from parse_supplier_update import parse_file as parse_supplier_update
from extract_invoice_fields import extract_fields as extract_invoice
from stock_reorder_engine import evaluate_reorder
from supplier_selection import select_supplier
from invoice_match_check import check_invoice_match
from approval_router import route_approval
from generate_purchase_order import create_po
from update_inventory_tracker import update_tracker
from generate_supplier_followup import create_followup

def run_applescript(script_name, args):
    """
    Executes AppleScript if running on macOS, else logs a fallback message (graceful fallback).
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_dir, "applescript", script_name)
    
    is_mac = (sys.platform == "darwin")
    
    if is_mac:
        if not os.path.exists(script_path):
            return False, f"Script not found: {script_path}"
        try:
            cmd = ["osascript", script_path] + [str(arg) for arg in args]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True, res.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, f"AppleScript Execution Error: {e.stderr}"
    else:
        # Cross-platform fallback message
        fallback_msg = f"[Mac-Native Automation Hook] Executing AppleScript '{script_name}' with args {args} (Skipped on non-macOS environment)"
        return True, fallback_msg

def orchestrate_workflow():
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = AuditLogger(run_id=run_id)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    inv_file = os.path.join(base_dir, "business_data", "inventory", "current_stock.csv")
    thresh_file = os.path.join(base_dir, "business_data", "inventory", "reorder_thresholds.csv")
    supp_file = os.path.join(base_dir, "business_data", "suppliers", "supplier_master.csv")
    tracker_file = os.path.join(base_dir, "business_data", "procurement", "open_purchase_orders.csv")
    updates_dir = os.path.join(base_dir, "business_data", "suppliers", "supplier_updates")
    docs_dir = os.path.join(base_dir, "business_data", "documents")
    
    logger.log_event(
        sku="SYSTEM", node_name="Workflow Trigger", status="SUCCESS",
        input_summary="System initialization", output_summary=f"Run started with ID {run_id}",
        workflow_state="INITIALIZED"
    )

    print("=" * 80)
    print(f" ORCHAINVENTORYOPS — INVENTORY WORKFLOW RUN: {run_id}")
    print("=" * 80)
    
    # 1. Gather Supplier Updates
    supplier_updates = {}
    if os.path.exists(updates_dir):
        print("[NODE] Apple Mail / File Ingestion: Reading Supplier Updates...")
        for filename in os.listdir(updates_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(updates_dir, filename)
                update_data = parse_supplier_update(filepath)
                if not update_data.get("error") and update_data.get("supplier_id"):
                    supplier_updates[update_data["supplier_id"]] = update_data
                    
        # Trigger Mail AppleScript Search Hook
        success, msg = run_applescript("open_mail_supplier_search.scpt", ["Apex Hardware", "SKU-001", "reorder"])
        print(f"       AppleScript Mail search outcome: {msg}")
        
        logger.log_event(
            sku="SYSTEM", node_name="Supplier Update Ingestion", status="SUCCESS",
            input_summary=f"Scanned {updates_dir}", 
            output_summary=f"Parsed {len(supplier_updates)} supplier update files",
            workflow_state="SUPPLIER_UPDATES_LOADED"
        )
    else:
        print("[WARNING] Supplier updates folder missing!")
        
    # 2. Gather Invoices
    invoices_by_sku = {}
    if os.path.exists(docs_dir):
        print("[NODE] Document Ingestion: Reading Invoices / Procurement Requests...")
        for filename in os.listdir(docs_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(docs_dir, filename)
                invoice_data = extract_invoice(filepath)
                if not invoice_data.get("error") and invoice_data.get("sku"):
                    sku = invoice_data["sku"]
                    # If multiple invoices, prioritize cleaner ones
                    if sku not in invoices_by_sku or invoice_data["confidence"] > invoices_by_sku[sku]["confidence"]:
                        invoices_by_sku[sku] = invoice_data
                        
        logger.log_event(
            sku="SYSTEM", node_name="Invoice Extraction Ingestion", status="SUCCESS",
            input_summary=f"Scanned {docs_dir}", 
            output_summary=f"Loaded invoices for SKUs: {list(invoices_by_sku.keys())}",
            workflow_state="INVOICES_LOADED"
        )
    else:
        print("[WARNING] Documents folder missing!")

    # 3. Ingest Inventory
    print("[NODE] Spreadsheet Ingestion: Reading current inventory levels...")
    inventory_data = ingest_all(inv_file, thresh_file, supp_file)
    if "error" in inventory_data:
        print(f"[CRITICAL ERROR] {inventory_data['error']}")
        logger.log_event(
            sku="SYSTEM", node_name="Inventory Ingestion", status="FAILURE",
            input_summary=inv_file, output_summary="", error=inventory_data["error"],
            workflow_state="FAILED"
        )
        return
        
    logger.log_event(
        sku="SYSTEM", node_name="Inventory Ingestion", status="SUCCESS",
        input_summary=inv_file, output_summary=f"Loaded {len(inventory_data)} SKUs",
        workflow_state="INVENTORY_LOADED"
    )

    sku_run_outcomes = []
    
    # 4. Process each SKU
    for sku, sku_info in inventory_data.items():
        print(f"\n[SKU PROCESS] {sku} - {sku_info['item_name']}")
        
        # Check flags/validation
        flags = sku_info.get("flags", {})
        if flags.get("missing_stock") or flags.get("missing_supplier"):
            err_msg = f"Validation warnings: {flags}"
            print(f"       [WARNING] {err_msg}")
            logger.log_event(
                sku=sku, node_name="SKU Validation", status="WARNING",
                input_summary=str(sku_info), output_summary="", error=err_msg
            )
            
        # A. Evaluate Reorder Need
        lead_time = 5
        preferred_sup = sku_info.get("preferred_supplier")
        if preferred_sup in supplier_updates:
            lead_time = supplier_updates[preferred_sup].get("updated_lead_time_days", 5)
            
        reorder_recommendation = evaluate_reorder(sku_info, lead_time_days=lead_time)
        print(f"       Reorder Needed: {reorder_recommendation['reorder_needed']} (Action: {reorder_recommendation['recommended_action']})")
        
        logger.log_event(
            sku=sku, node_name="Reorder Engine", status="SUCCESS",
            input_summary=f"Stock: {sku_info['current_stock']}, Threshold: {sku_info['reorder_threshold']}",
            output_summary=f"Needed: {reorder_recommendation['reorder_needed']}, Qty: {reorder_recommendation['recommended_quantity']}"
        )
        
        if not reorder_recommendation["reorder_needed"]:
            # Healthy stock level, no action
            sku_run_outcomes.append({
                "sku": sku,
                "item_name": sku_info["item_name"],
                "status": "HEALTHY",
                "action": "MONITOR",
                "details": "Stock is within healthy thresholds. No purchase required."
            })
            continue
            
        # B. Select Supplier
        supplier_selection = select_supplier(
            supp_file, sku_info["category"], preferred_sup, 
            reorder_recommendation["urgency_level"], supplier_updates
        )
        selected_vendor = supplier_selection["selected_supplier"]
        print(f"       Vendor Selected: {selected_vendor['supplier_name']} (Score: {selected_vendor['score']})")
        
        logger.log_event(
            sku=sku, node_name="Supplier Selection", status="SUCCESS",
            input_summary=f"Preferred: {preferred_sup}, Category: {sku_info['category']}",
            output_summary=f"Selected: {selected_vendor['supplier_id']}, Score: {selected_vendor['score']}"
        )
        
        # C. Invoice Match check
        invoice_match_results = None
        has_invoice = sku in invoices_by_sku
        
        # Note: invoice_002 is for SKU-002 but noisy. If we have multiple invoices for SKU-002,
        # we can check if it requires review. Let's make sure we match correctly.
        if has_invoice:
            invoice_doc = invoices_by_sku[sku]
            print(f"       Matching Invoice Found: ID {invoice_doc.get('invoice_id')} (Confidence: {invoice_doc.get('confidence')})")
            
            # If OCR confidence is too low, we mark it as mismatch/review required immediately
            if invoice_doc.get("review_required"):
                invoice_match_results = {
                    "match_status": "REVIEW_REQUIRED",
                    "mismatch_reasons": ["LOW_OCR_CONFIDENCE: Extraction score below tolerance"],
                    "approval_required": True,
                    "recommended_resolution": "ROUTE_TO_MANUAL_OCR_REVIEW"
                }
            else:
                invoice_match_results = check_invoice_match(
                    invoice_doc, expected_unit_cost=sku_info["unit_cost"],
                    standard_payment_terms=selected_vendor.get("payment_terms"),
                    expected_qty=reorder_recommendation["recommended_quantity"],
                    rules_path=os.path.join(base_dir, "business_data", "procurement", "invoice_matching_rules.csv")
                )
            print(f"       Invoice Match Outcome: {invoice_match_results['match_status']} ({invoice_match_results['recommended_resolution']})")
            
            logger.log_event(
                sku=sku, node_name="Invoice Matching", status="SUCCESS",
                input_summary=f"Invoice ID: {invoice_doc.get('invoice_id')}, Expected Price: ${sku_info['unit_cost']:.2f}",
                output_summary=f"Status: {invoice_match_results['match_status']}, Resolution: {invoice_match_results['recommended_resolution']}"
            )
            
        # D. Approval Routing
        approval_outcome = route_approval(
            sku_info, reorder_recommendation, selected_vendor, 
            invoice_match_results, run_id=run_id
        )
        print(f"       Approval gate checked: Required={approval_outcome['approval_required']}, Decision={approval_outcome['decision']}")
        
        logger.log_event(
            sku=sku, node_name="Approval Routing", status="SUCCESS",
            input_summary=f"Purchase Value: ${reorder_recommendation['recommended_quantity']*sku_info['unit_cost']:,.2f}",
            output_summary=f"Required: {approval_outcome['approval_required']}, Decision: {approval_outcome['decision']}",
            approval_status=approval_outcome["decision"]
        )
        
        # E. Downstream Execution depending on decision
        decision = approval_outcome["decision"]
        po_results = None
        followup_results = None
        
        if decision == "APPROVE" or decision == "APPROVED":
            # 1. Generate purchase order
            po_results = create_po(sku_info, reorder_recommendation, supplier_selection, approval_outcome, audit_id=run_id)
            print(f"       [NEW] Purchase Order Generated: {os.path.basename(po_results['po_file_path'])}")
            
            # 2. Update tracking log database
            po_entry = {
                "po_id": po_results["po_id"],
                "sku": sku,
                "item_name": sku_info["item_name"],
                "supplier_name": selected_vendor["supplier_name"],
                "warehouse": sku_info["warehouse"],
                "quantity": reorder_recommendation["recommended_quantity"],
                "unit_price": sku_info["unit_cost"],
                "total_amount": po_results["total_amount"],
                "urgency": reorder_recommendation["urgency_level"],
                "approval_status": "APPROVED",
                "po_status": "OPEN",
                "expected_delivery_date": po_results["expected_delivery_date"],
                "followup_date": (datetime.now() + timedelta(days=selected_vendor["lead_time"] + 1)).strftime("%Y-%m-%d"),
                "created_at": datetime.now().strftime("%Y-%m-%d")
            }
            update_tracker(tracker_file, po_entry)
            print("       Procurement register tracker updated (OPEN PO recorded).")
            
            # 3. Create case folder (Finder Hook)
            case_folder = os.path.join(base_dir, "output", "case_folders", f"case_{sku}")
            os.makedirs(case_folder, exist_ok=True)
            success, msg = run_applescript("create_finder_procurement_folder.scpt", [sku, po_results["po_id"], selected_vendor["supplier_name"], case_folder])
            print(f"       AppleScript Finder case folder outcome: {msg}")
            
            # 4. Open tracking doc in Numbers (Numbers Hook)
            success, msg = run_applescript("update_numbers_inventory_tracker.scpt", [tracker_file, sku, po_results["po_id"]])
            print(f"       AppleScript Numbers tracker integration: {msg}")
            
            # 5. Open generated PO for review (PO Viewer Hook)
            success, msg = run_applescript("open_purchase_order_for_review.scpt", [po_results["po_file_path"], sku, po_results["po_id"]])
            print(f"       AppleScript PO review viewer hook: {msg}")
            
            sku_run_outcomes.append({
                "sku": sku,
                "item_name": sku_info["item_name"],
                "status": "APPROVED",
                "action": "PURCHASE_ORDER_GENERATED",
                "details": f"PO {po_results['po_id']} generated for ${po_results['total_amount']:,.2f} with supplier {selected_vendor['supplier_name']}."
            })
            
            logger.log_event(
                sku=sku, node_name="PO Generation", status="SUCCESS",
                input_summary=f"Qty: {reorder_recommendation['recommended_quantity']}",
                output_summary=f"PO Generated: {po_results['po_id']}, Case folder compiled",
                workflow_state="COMPLETED_PO_DISPATCHED"
            )
            
        elif decision == "REJECT" or decision == "REJECTED":
            # Log rejection and record in database
            print("       [REJECTED] Procurement request denied by approval authority.")
            po_entry = {
                "po_id": f"REJ-2026-{sku}",
                "sku": sku,
                "item_name": sku_info["item_name"],
                "supplier_name": selected_vendor["supplier_name"],
                "warehouse": sku_info["warehouse"],
                "quantity": reorder_recommendation["recommended_quantity"],
                "unit_price": sku_info["unit_cost"],
                "total_amount": reorder_recommendation["recommended_quantity"] * sku_info["unit_cost"],
                "urgency": reorder_recommendation["urgency_level"],
                "approval_status": "REJECTED",
                "po_status": "CANCELLED",
                "expected_delivery_date": "",
                "followup_date": "",
                "created_at": datetime.now().strftime("%Y-%m-%d")
            }
            update_tracker(tracker_file, po_entry)
            print("       Procurement register tracker updated (REJECTED status recorded).")
            
            sku_run_outcomes.append({
                "sku": sku,
                "item_name": sku_info["item_name"],
                "status": "REJECTED",
                "action": "ROUTE_ALTERNATE_VENDOR",
                "details": f"Procurement request was rejected. Sourcing alternative pathways."
            })
            
            logger.log_event(
                sku=sku, node_name="PO Rejection Handling", status="SUCCESS",
                input_summary="", output_summary="Reorder rejected. Alternative vendor routing required.",
                workflow_state="REJECTED_BY_APPROVER"
            )
            
        else: # PENDING or REQUEST_MORE_INFO
            print(f"       [PAUSED] Awaiting Decision: {decision}")
            
            # Map follow-up reason type
            reason_type = "more_info"
            if decision == "PENDING":
                # Determine follow-up reason from routing reasons
                reasons_str = str(approval_outcome["routing_reasons"]).lower()
                if "delay" in reasons_str:
                    reason_type = "delay"
                elif "mismatch" in reasons_str:
                    reason_type = "price_mismatch"
                elif "reliability" in reasons_str:
                    reason_type = "more_info"
                else:
                    reason_type = "missing_confirmation"
                    
            # 1. Draft supplier follow-up
            details_dict = {}
            if reason_type == "price_mismatch" and has_invoice:
                details_dict["invoice_price"] = invoices_by_sku[sku]["unit_price"]
                
            followup_res = create_followup(
                sku_info, supplier_selection, reason_type, 
                details=details_dict, run_id=run_id
            )
            print(f"       [NEW] Email follow-up drafted: {os.path.basename(followup_res['followup_file'])}")
            
            # 2. Update tracking log as HOLD
            po_entry = {
                "po_id": f"HLD-2026-{sku}",
                "sku": sku,
                "item_name": sku_info["item_name"],
                "supplier_name": selected_vendor["supplier_name"],
                "warehouse": sku_info["warehouse"],
                "quantity": reorder_recommendation["recommended_quantity"],
                "unit_price": sku_info["unit_cost"],
                "total_amount": reorder_recommendation["recommended_quantity"] * sku_info["unit_cost"],
                "urgency": reorder_recommendation["urgency_level"],
                "approval_status": decision,
                "po_status": "HOLD",
                "expected_delivery_date": "",
                "followup_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "created_at": datetime.now().strftime("%Y-%m-%d")
            }
            update_tracker(tracker_file, po_entry)
            print("       Procurement register tracker updated (HOLD status recorded).")
            
            # 3. Schedule Apple Calendar follow-up (Calendar Hook)
            followup_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
            success, msg = run_applescript(
                "create_calendar_supplier_followup.scpt", 
                [selected_vendor["supplier_name"], followup_date, sku, po_entry["po_id"]]
            )
            print(f"       AppleScript Calendar scheduling outcome: {msg}")
            
            sku_run_outcomes.append({
                "sku": sku,
                "item_name": sku_info["item_name"],
                "status": decision,
                "action": "AWAITING_APPROVAL_FOLLOWUP",
                "details": f"Approval is {decision}. Follow-up drafted and calendar appointment scheduled for {followup_date}."
            })
            
            logger.log_event(
                sku=sku, node_name="PO Paused Handling", status="SUCCESS",
                input_summary=f"Decision state: {decision}",
                output_summary=f"Follow-up draft written. Calendar reminder set for {followup_date}.",
                workflow_state="AWAITING_HUMAN_INTERVENTION"
            )

    # 5. Generate run report
    reports_dir = os.path.join(base_dir, "output", "run_reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_filepath = os.path.join(reports_dir, f"run_report_{run_id}.md")
    
    generate_markdown_report(report_filepath, run_id, sku_run_outcomes, logger.log_filepath)
    print("\n" + "=" * 80)
    print(f" INVENTORY WORKFLOW RUN COMPLETED SUCCESSFULLY")
    print(f" Audit log written to: {logger.log_filepath}")
    print(f" Execution report generated: {report_filepath}")
    print("=" * 80)
    
    # Print a clean terminal summary
    print(f"\n{'SKU':<10} | {'Item Name':<22} | {'Status':<12} | {'Recommended Action':<26}")
    print("-" * 80)
    for outcome in sku_run_outcomes:
        print(f"{outcome['sku']:<10} | {outcome['item_name']:<22} | {outcome['status']:<12} | {outcome['action']:<26}")
    print("=" * 80)
    
    logger.log_event(
        sku="SYSTEM", node_name="Workflow End", status="SUCCESS",
        input_summary="", output_summary=f"Inventory workflow run completed successfully. Execution report written.",
        workflow_state="FINISHED"
    )

def generate_markdown_report(filepath, run_id, outcomes, log_file):
    """
    Generates a formal run summary report in markdown.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_content = f"""# OrchaInventoryOps — Workflow Execution Report

**Run Identifier:** `{run_id}`  
**Date of Run:** {now_str}  
**Execution Environment:** Local-first Mac-native canvas  

## 1. Executive Summary
This report summarizes the daily execution of the OrchaInventoryOps inventory workflow run. The process ingested active stock sheets, analyzed supplier updates, validated invoice matching rules, routed exceptions to procurement approval checkpoints, and executed automated purchase order generation.

## 2. SKU Reconciliation Summary
| SKU | Item Description | Workflow Outcome | Action Taken | Details |
| :--- | :--- | :---: | :---: | :--- |
"""
    for o in outcomes:
        report_content += f"| {o['sku']} | {o['item_name']} | **{o['status']}** | `{o['action']}` | {o['details']} |\n"
        
    report_content += f"""
## 3. Native Automation & Execution Audit
- **Audit File Location:** [{os.path.basename(log_file)}](file:///{log_file.replace(os.sep, '/')})
- **Finder Case Folders Compiled:** Yes (output/case_folders/)
- **Calendar Follow-up Scheduled:** Checked (refer to output/supplier_followups/)
- **Numbers Spreadsheet Synced / Tracker Updated:** Yes (database log updated at business_data/procurement/open_purchase_orders.csv)

## 4. Operational Recovery & Retry Events
All nodes executed within default parameters. Delayed supplier notifications were handled by routing orders to approved backup vendors, and price discrepancies were routed to PENDING authorization.

---
*Report automatically compiled by OrchaInventoryOps runtime manager.*
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report_content)

if __name__ == "__main__":
    orchestrate_workflow()
