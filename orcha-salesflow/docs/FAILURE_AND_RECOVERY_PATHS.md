# Failure and Recovery Paths: Self-Healing Architecture

This document outlines the self-healing recovery actions and exception handling pathways built into the **OrchaSalesFlow** workflow implementation.

---

## 🛠️ Detailed Failure Recovery Matrix

### 1. Incomplete Intake (Missing Budget)
* **Trigger Condition**: Lead intake email does not specify budget parameters.
* **Detection Node**: `node_parse_email` returns `budget: null`.
* **Recovery Action**: `node_check_budget_presence` routes the thread to `node_clarification_path`. The system compiles a clarification email request instead of a proposal.
* **Audit Log Event**: `BUDGET_MISSING_ROUTING`
* **Final Workflow State**: `CLARIFICATION_SENT` (Needs Discovery stage in CRM).

### 2. Corrupted Text (Low-Confidence OCR)
* **Trigger Condition**: Scanned quote attachment text contains spelling corruption.
* **Detection Node**: `node_extract_quote_fields` calculates `ocr_confidence < 0.70`.
* **Recovery Action**: `node_check_ocr_confidence` routes to `node_ocr_retry_fallback`. A cleanup dictionary repairs spelling substitutions (e.g. `Sp4rk` -> `Spark`) and boosts confidence metrics to 85% to permit continuation.
* **Audit Log Event**: `OCR_CORRECTION_APPLIED`
* **Final Workflow State**: `PROPOSAL_COMPILED` (Proceeds along standard path).

### 3. Missing Quote Attachment
* **Trigger Condition**: Intake email references an attachment but no file is present in the watch directory.
* **Detection Node**: `node_ocr_quote` detects file absence.
* **Recovery Action**: Skip OCR extraction nodes. Score the lead based on email body parameters alone. Assign a default confidence value for scoring calculations.
* **Audit Log Event**: `ATTACHMENT_MISSING_WARNING`
* **Final Workflow State**: `PROPOSAL_COMPILED` (Compiles proposal with default catalog scope).

### 4. Pricing Exceptions
* **Trigger Condition**: Requested discount rate exceeds the approved threshold (15%).
* **Detection Node**: `node_pricing_check` returns `approval_required: true`.
* **Recovery Action**: Route lead records to `node_human_approval_checkpoint`. Halt the thread, output a risk report, and wait for a manager's decision file.
* **Audit Log Event**: `EXCEPTION_DETECTION`
* **Final Workflow State**: `PENDING_APPROVAL` (Awaiting manager action).

### 5. Non-Standard Contract Terms
* **Trigger Condition**: Quote requests payment terms other than Net 30 (e.g. Net 60, Net 90).
* **Detection Node**: `node_pricing_check` identifies terms exception.
* **Recovery Action**: Flags compliance exception, routes to `node_human_approval_checkpoint`, and halts execution for manual review.
* **Audit Log Event**: `TERMS_EXCEPTION_FLAGGED`
* **Final Workflow State**: `PENDING_APPROVAL` (Awaiting review).

### 6. Approval Rejected
* **Trigger Condition**: Manager logs a `REJECT` decision at the approval checkpoint.
* **Detection Node**: `node_human_approval_checkpoint` receives `REJECT`.
* **Recovery Action**: Bypass proposal generation nodes. Route lead to `node_update_crm_disqualified` to mark status as Closed Lost.
* **Audit Log Event**: `APPROVAL_REJECTED`
* **Final Workflow State**: `DISQUALIFIED` (Closed Lost stage in CRM).

### 7. Approval Requests More Information
* **Trigger Condition**: Manager logs a `REQUEST_MORE_INFO` decision at the checkpoint.
* **Detection Node**: `node_human_approval_checkpoint` receives `REQUEST_MORE_INFO`.
* **Recovery Action**: Route to `node_clarification_path`. Compile a clarification inquiry letter to request information.
* **Audit Log Event**: `APPROVAL_CLARIFY_REQUESTED`
* **Final Workflow State**: `CLARIFICATION_SENT` (Information Request stage in CRM).

### 8. Duplicate CRM Entries
* **Trigger Condition**: Script is re-run on a lead record that has already been registered in the CRM.
* **Detection Node**: `node_update_crm_numbers` searches spreadsheet cells and finds matching `lead_id`.
* **Recovery Action**: Overwrite the fields in the existing row rather than appending a new row, ensuring database idempotency.
* **Audit Log Event**: `CRM_ROW_UPDATED`
* **Final Workflow State**: `SUCCESS` (Existing record updated, no duplicates).

### 9. Proposal Generation Failures
* **Trigger Condition**: File write permissions prevent exporting proposal markdown files to the proposals directory.
* **Detection Node**: `node_generate_proposal` returns exception.
* **Recovery Action**: Trigger 1 retry attempt. If it continues to fail, halt execution for that lead record and notify the system administrator.
* **Audit Log Event**: `PROPOSAL_COMPILATION_ERROR`
* **Final Workflow State**: `FAILED` (Logs error to audit trail, proceeds to next lead).

### 10. Calendar Scheduling Failures
* **Trigger Condition**: Access control blocks scheduling follow-up reminders.
* **Detection Node**: `node_create_calendar_followup` returns shell exit code.
* **Recovery Action**: Capture the error. Attempt 1 retry after activating the Calendar app. If it continues to fail, log a warning to the audit trail and continue, ensuring the sales process is not blocked.
* **Audit Log Event**: `CALENDAR_INTEGRATION_WARNING`
* **Final Workflow State**: `SUCCESS` (Lead finishes successfully, calendar warning logged).

### 11. AppleScript Permission Failures
* **Trigger Condition**: Native macOS accessibility or application control permissions are blocked.
* **Detection Node**: AppleScript node catches execution error.
* **Recovery Action**: Log the permission issue as a warning. Fallback to the Python-level CSV update, and continue with file-system operations.
* **Audit Log Event**: `APPLESCRIPT_PERMISSION_ERROR`
* **Final Workflow State**: `SUCCESS` (Data written to local files, warning logged for administration).

### 12. Partial Run Failures
* **Trigger Condition**: A single lead record triggers a compilation error or file read crash.
* **Detection Node**: High-level execution loop catches local exceptions.
* **Recovery Action**: Isolate the failing lead thread. Write the exception details to the audit logger, then proceed to the next lead in the directory queue, ensuring the runner finishes the remaining workload.
* **Audit Log Event**: `LEAD_RUN_EXCEPTION`
* **Final Workflow State**: `PARTIAL_SUCCESS` (Valid leads finish, failed leads logged).
