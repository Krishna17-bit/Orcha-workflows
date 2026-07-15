# Failure and Recovery Paths

The `OrchaInventoryOps` workflow is designed for maximum fault tolerance. This document maps the detection nodes, triggers, recovery actions, and final states for all potential exceptions in the workflow.

This workflow uses representative business records so the architecture, routing logic, approval model, and Mac-native automation pattern can be reviewed without exposing protected client information.


---

## 1. Missing Inventory Value
* **Trigger Condition:** A row in `current_stock.csv` lacks a `current_stock` quantity.
* **Detection Node:** `NODE-TRM-003` (ingest_inventory.py)
* **Recovery Action:** Set stock level to `0.0`, raise a `missing_stock` validation flag, and continue parsing.
* **Audit Log Event:** `SKU_VALIDATION` (Status: WARNING)
* **Final Workflow State:** Evaluated as `0` stock, leading to emergency reorder.

---

## 2. Missing Reorder Threshold
* **Trigger Condition:** A SKU in stock records lacks a matching row in `reorder_thresholds.csv`.
* **Detection Node:** `NODE-TRM-003` (ingest_inventory.py)
* **Recovery Action:** Apply system-wide default thresholds (minimum: `10`, target: `50`, urgent: `5`), raise `missing_threshold` flag, and continue.
* **Audit Log Event:** `SKU_VALIDATION` (Status: WARNING)
* **Final Workflow State:** Proceed to stock evaluation with default constraints.

---

## 3. Missing Supplier
* **Trigger Condition:** The preferred supplier ID listed for a SKU is blank or missing from `supplier_master.csv`.
* **Detection Node:** `NODE-TRM-003` (ingest_inventory.py)
* **Recovery Action:** Raise `missing_supplier` warning flag and skip custom vendor scoring. If a reorder is needed, select the first supplier that supports the product category in `supplier_master.csv`.
* **Audit Log Event:** `SKU_VALIDATION` (Status: WARNING)
* **Final Workflow State:** Resilient selection of category-compatible vendor.

---

## 4. Low-Confidence Invoice Extraction
* **Trigger Condition:** The invoice text extraction script returns a confidence rating below `0.70` (e.g. from noisy scanned files).
* **Detection Node:** `NODE-TRM-007` (extract_invoice_fields.py)
* **Recovery Action:** Mark document matching status as `REVIEW_REQUIRED` and route to human review.
* **Audit Log Event:** `INVOICE_MATCHING` (Status: REVIEW_REQUIRED)
* **Final Workflow State:** Workflow pauses on `PENDING` decision for the SKU; drafts manual OCR review follow-up.

---

## 5. Missing Invoice Field
* **Trigger Condition:** Extracted invoice data lacks mandatory fields (invoice number, total cost, or SKU).
* **Detection Node:** `NODE-TRM-007` (extract_invoice_fields.py)
* **Recovery Action:** Set match status to `REVIEW_REQUIRED` and raise `MISSING_INVOICE_FIELDS` reason code.
* **Audit Log Event:** `INVOICE_MATCHING` (Status: REVIEW_REQUIRED)
* **Final Workflow State:** Awaiting human checkpoint clearance.

---

## 6. Price Mismatch
* **Trigger Condition:** Extracted invoice unit price exceeds expectation by more than the 2% tolerance limit.
* **Detection Node:** `NODE-TRM-010` (invoice_match_check.py)
* **Recovery Action:** Flag `UNIT_PRICE_MISMATCH`, mark match status as `MISMATCH`, and route to the Finance Director for approval.
* **Audit Log Event:** `INVOICE_CHECK_COMPLETE` (Status: MISMATCH)
* **Final Workflow State:** Paused; drafts billing variance follow-up and sets calendar reminder.

---

## 7. Supplier Delay
* **Trigger Condition:** Ingested supplier update reports shipping delays or expanded lead times.
* **Detection Node:** `NODE-TRM-005` (parse_supplier_update.py)
* **Recovery Action:** The selection matrix applies a `-80` point penalty to the delayed supplier and adjusts their lead time. It ranks alternative suppliers and selects the backup vendor.
* **Audit Log Event:** `SUPPLIER_RECONCILIATION_FINISHED` (Status: SUCCESS)
* **Final Workflow State:** Procurement routed to backup supplier to prevent stockout.

---

## 8. Supplier Price Change
* **Trigger Condition:** Supplier communication reports catalog price adjustment.
* **Detection Node:** `NODE-TRM-005` (parse_supplier_update.py)
* **Recovery Action:** Apply score penalty to preferred vendor based on increase percent; recalculate safety margins.
* **Audit Log Event:** `SUPPLIER_RECONCILIATION_FINISHED` (Status: SUCCESS)
* **Final Workflow State:** If alternative vendors are cheaper, selects backup; otherwise proceeds with price change and logs warning.

---

## 9. Critical Stockout Risk
* **Trigger Condition:** Stock level drops below urgent threshold or remaining days of stock is less than supplier lead time.
* **Detection Node:** `NODE-TRM-008` (stock_reorder_engine.py)
* **Recovery Action:** Escalate urgency to `CRITICAL` and set action to `EXPEDITE_REORDER`.
* **Audit Log Event:** `REORDER_RECOMMENDATION_CALCULATED` (Status: SUCCESS)
* **Final Workflow State:** Triggers urgent approval routing.

---

## 10. High-Value Procurement Approval
* **Trigger Condition:** Order cost exceeds standard authorization limit (e.g. $10,000.00).
* **Detection Node:** `NODE-TRM-013` (approval_router.py)
* **Recovery Action:** Generate detailed approval request markdown report and route to `VP of Operations`.
* **Audit Log Event:** `APPROVAL_FORM_PUBLISHED` (Status: AWAITING_DECISION)
* **Final Workflow State:** Pauses execution pending sign-off in `approval_decision_{sku}.txt`.

---

## 11. Approval Rejected
* **Trigger Condition:** The approval decision file reads `REJECT`.
* **Detection Node:** `NODE-HMN-014` (Human Approval Checkpoint)
* **Recovery Action:** Log rejection in PO database with status `CANCELLED` and stop purchase order compilation.
* **Audit Log Event:** `HUMAN_DECISION_REGISTERED` (Status: REJECTED)
* **Final Workflow State:** Workflow path terminates gracefully for this SKU.

---

## 12. Approval Requests More Info
* **Trigger Condition:** The approval decision file reads `REQUEST_MORE_INFO`.
* **Detection Node:** `NODE-HMN-014` (Human Approval Checkpoint)
* **Recovery Action:** Draft a supplier clarification email, set PO status to `HOLD`, and schedule a calendar check.
* **Audit Log Event:** `HUMAN_DECISION_REGISTERED` (Status: REQUEST_MORE_INFO)
* **Final Workflow State:** Awaiting supplier reply.

---

## 13. Duplicate Purchase Order
* **Trigger Condition:** The orchestrator attempts to generate a purchase order that has already been registered in the database.
* **Detection Node:** `NODE-TRM-016` (update_inventory_tracker.py)
* **Recovery Action:** Run idempotent check. Update existing record with latest timestamps rather than appending a duplicate row.
* **Audit Log Event:** `OPEN_ORDER_TRACKER_UPDATED` (Status: SUCCESS, Action: UPDATE)
* **Final Workflow State:** Clean transaction data maintained.

---

## 14. Purchase Order Generation Failure
* **Trigger Condition:** File permissions or directory locking prevents writing PO markdown file.
* **Detection Node:** `NODE-TRM-015` (generate_purchase_order.py)
* **Recovery Action:** Log write error, catch exception, and raise system alert.
* **Audit Log Event:** `PO_GENERATION` (Status: FAILURE)
* **Final Workflow State:** Continues processing remaining SKUs; flags current SKU path as failed.

---

## 15. Calendar Follow-Up Creation Failure
* **Trigger Condition:** AppleScript execution fails or is blocked while creating Calendar reminder.
* **Detection Node:** `NODE-APP-022` (Create Calendar Supplier Follow-up)
* **Recovery Action:** Catch exception, log parameters to terminal and audit logs, and continue.
* **Audit Log Event:** `CALENDAR_EVENT_SCHEDULED` (Status: WARNING)
* **Final Workflow State:** Proceed to workflow end without crashing the run.

---

## 16. AppleScript Permission / Accessibility Failure
* **Trigger Condition:** Script execution fails due to macOS sandboxing or disabled accessibility permissions.
* **Detection Node:** AppleScript execution nodes (`osascript`)
* **Recovery Action:** Execute cross-platform fallback logic: write log detail to standard output and continue.
* **Audit Log Event:** Script execution events (Status: WARNING)
* **Final Workflow State:** Graceful fallback ensures uninterrupted automated execution.

---

## 17. Partial Run Failure (Resiliency)
* **Trigger Condition:** An exception crashes execution for a specific SKU.
* **Detection Node:** `run_inventoryops.py` loop handler
* **Recovery Action:** Wrap SKU processing block in try-except block. Catch the error, log to audit log, and proceed to next SKU.
* **Audit Log Event:** `SKU_PROCESS` (Status: FAILURE)
* **Final Workflow State:** Surviving SKUs complete execution successfully.
