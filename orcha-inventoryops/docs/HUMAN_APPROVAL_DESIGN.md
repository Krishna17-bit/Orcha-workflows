# Human Approval Design

This document details the visual human-in-the-loop gates used in the `OrchaInventoryOps` workflow, explaining the file-based checkpoint system and compliance thresholds.

This workflow uses representative business records so the architecture, routing logic, approval model, and Mac-native automation pattern can be reviewed without exposing protected client information.


## 1. Why Human Approval Exists
Automating procurement must balance efficiency with policy enforcement. While routine, low-value inventory replenishment is fully automated, critical decisions involving substantial expense, pricing mismatches, or supplier risks require authorized review to prevent compliance issues.

## 2. Procurement Decisions Requiring Approval
The workflow flags and routes items to manual checkpoints based on the following criteria:
* **High-Value Orders:** Orders exceeding the SKU-specific approval limit (e.g. $10,000.00 for turbine rotors, or standard $5,000.00 for hardware).
* **Critical Stockouts:** Expedited orders where remaining stock is below critical limits and total cost exceeds $1,000.00.
* **Invoice Price Mismatch:** Extracted invoice prices that deviate from master records by more than 2%.
* **Low Supplier Score:** Reorders placed with a supplier whose reliability score is below 0.90.
* **Low OCR Confidence:** Billing documents with extraction confidence below 0.70.

---

## 3. Local File-Based Checkpoint Structure
The workflow emulates Orcha's manual checkpoint capability using local directory watchers:
1. **Request Publishing:** The approval router writes a detailed markdown summary to:  
   `output/approvals/approval_request_{sku}.md`
2. **Checkpoint File:** The router creates a corresponding decision signature file:  
   `output/approvals/approval_decision_{sku}.txt`
3. **Polling Loop:** The canvas node watches this directory. Downstream tasks are paused for this SKU until an operator writes a valid decision keyword into the decision file.

### Valid Decision Keywords (Uppercase, first line of text file):
* `APPROVE` — Clears the order for compilation and dispatch.
* `REJECT` — Cancels the request and updates the ledger status.
* `REQUEST_MORE_INFO` — Pauses the order, drafts supplier follow-up clarification, and schedules a calendar check.
* `PENDING` — Initial state; continues to hold order until review is complete.

---

## 4. Downstream Workflow Routing

```
                     +---------------------------+
                     |  manual decision file     |
                     +-------------+-------------+
                                   |
           +-----------------------+-----------------------+
           |                       |                       |
      [ APPROVED ]            [ REJECTED ]        [ REQUEST_MORE_INFO ]
           |                       |                       |
           v                       v                       v
+----------------------+ +-------------------+ +-----------------------+
| Generate PO file     | | Set PO: CANCELLED | | Set PO: HOLD          |
| Set PO: OPEN         | | Audit: REJECTED   | | Draft supplier email  |
| Update Numbers sheet | | Halts SKU path    | | Set Calendar check    |
| Focus Finder folder  | +-------------------+ +-----------------------+
+----------------------+
```

---

## 5. Walkthrough Cases

### Example 1: SKU-003 Critical Stockout Approval
* **Condition:** Current stock is 5, below the reorder threshold of 30. Safety safety days remaining is ~1 day. Urgency is escalated to `CRITICAL`. Expected cost: $3,375.00.
* **Routing Reason:** Urgency is critical and value is above $1,000.00 safety barrier.
* **Action:** Approval request form created. If `approval_decision_SKU-003.txt` is updated to `APPROVE`, downstream scripting completes the PO generation, files it in case folders, and logs it in the database.

### Example 2: SKU-006 High-Value Procurement Approval
* **Condition:** Turbine Rotors require replenishment. Target reorder quantity is 8. Unit price is $3,500.00, totaling $28,000.00.
* **Routing Reason:** Purchase value exceeds $10,000.00 authorization limit.
* **Action:** Detailed markdown request compiled for VP of Operations review. With decision signature set to `APPROVE`, the workflow completes the order, creates folder structures, and displays the document in TextEdit.
