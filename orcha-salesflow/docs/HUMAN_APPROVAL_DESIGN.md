# Human-in-the-Loop Approval Checkpoint Design

This document details the architectural layout of the **Human-in-the-Loop (HITL) Approval Checkpoint** within the **OrchaSalesFlow** workflow implementation.

---

## 1. Why Human Approval Exists
While automation accelerates routine operations, financial and legal commitments carry business risks. Fully automated quoting can lead to margin erosion if excessive discounts are generated, or terms are accepted that expose the company to cash flow issues. Orcha addresses this by enforcing **manual review checkpoints** for high-risk exceptions.

---

## 2. Decisions Requiring Manual Review
The workflow flags three categories of exceptions for manager review:
1. **Discount Rate Thresholds**: Any discount request exceeding the standard 15% limit.
2. **Deal Budget Thresholds**: Lead budgets below the minimum catalog price defined in `product_catalog.csv`.
3. **Non-Standard Payment Terms**: Payment terms requesting periods longer than the Net 30 standard (e.g. Net 60 or Net 90).

---

## 3. Approval File Structure
When an exception occurs, Orcha writes an approval request report to `output/approvals/approval_request_<lead_id>.md`. This file contains:
* **Exceptions Log**: Bulleted warning list of compliance rule violations.
* **Financial Details**: Base catalog prices, requested discounts, proposed total values, and payment terms.
* **Countervailing Recommendation**: Suggested response based on rules catalogs (e.g., standard pricing countermeasures).
* **Instruction Checklist**: Guidelines on how to register the decision file to resume execution.

---

## 4. Decision Options
Managers resolve the checkpoint using three commands:
* **APPROVE**: Authorizes the exception. Orcha generates the proposal with an approved pricing watermark and updates the CRM status to `Proposal Preparation`.
* **REJECT**: Declines the exception. Orcha skips proposal generation, updates the CRM stage to `Closed Lost`, and routes the record to email nurturing.
* **REQUEST_MORE_INFO**: Suspends the proposal. Orcha generates an email requesting clarification on terms, updating the CRM stage to `Information Request`.

---

## 5. Mapping to Orcha's Canvas Node
On the visual Orcha builder:
* The exception is caught by a **Pricing Exception Gate** node.
* It routes the lead to a **Human Approval Checkpoint** node.
* In Orcha's web dashboard, this displays as a review card showing the risk factors, proposal draft, and action buttons (`APPROVE` / `REJECT` / `CLARIFY`).
* In local desktop environments, this is implemented using a file handshake: Orcha polls the directory for the presence of the `approval_decision.txt` file containing the decision content.

---

## 6. Audit Trail for Decisions
Every approval action is tracked in the execution log:
* State transitions are written to the JSONL log file: `timestamp`, `run_id`, `lead_id`, `node_name: "Human Approval Node"`, and `status: "PENDING"` followed by `status: "SUCCESS"` once resolved.
* The audit log captures the manager's decision string (`APPROVE` or `REJECT`) and links it to the final proposal and CRM updates for compliance audits.

---

## 7. Operational Example: LEAD-004
1. **Intake Processing**: Horizon Logistics requests a 25% discount and Net 90 payment terms for a Security Implementation.
2. **Pricing Verification**: The checker flags both items as exceptions.
3. **Checkpoint Halt**: The execution halts. `approval_request_LEAD-004.md` is compiled on disk.
4. **Resolution**: The manager reviews the report, resolves the checkpoint, and inputs `APPROVE`.
5. **Execution Resume**: Orcha resumes, compile the proposal with theApproved pricing watermark, updates Apple Numbers cells, and schedules follow-up tasks.
