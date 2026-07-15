# OrchaSalesFlow — Mac-Native Sales Pipeline Automation

This repository provides a local-first sales operations automation template. It shows how the Orcha Canvas coordinates tasks across local macOS applications.

This workflow implementation uses representative privacy-safe business records to execute processes without requiring external database or email API keys.

---

## 1. What This Workflow Does
The sales operations workflow automates the following lifecycle steps:
1. **Intake**: Watches folders for incoming client request texts.
2. **Extraction**: Integrates OCR parsing filters to scan procurement specifications.
3. **Scoring**: Applies lead qualification algorithms to evaluate target segments.
4. **Policy Enforcement**: Runs pricing check nodes to enforce discount margins.
5. **Human Safeguards**: Suspends execution at approval checkpoints when exceptions occur.
6. **Proposal Compiling**: Generates client proposals from formatted templates.
7. **CRM Sync**: Idempotently logs pipeline statuses to local spreadsheet files.
8. **Scheduling**: Interacts with local calendar applications to schedule reminders.
9. **Log Compliance**: Emits formatted JSONL trails for execution auditing.

---

## 2. System Architecture
The architecture mimics a visual workflow orchestrator containing scheduled triggers, terminal script nodes, conditional logic, and native desktop integration hooks:
* **Visual Blueprint Mapping**: Defined in [ORCHA_WORKFLOW_BLUEPRINT.md](ORCHA_WORKFLOW_BLUEPRINT.md) and mapped systematically via [ORCHA_NODE_MAP.json](ORCHA_NODE_MAP.json).
* **Mac-Native App Automation**: AppleScript wrappers communicate directly with macOS Finder, Mail, Numbers, and Calendar.
* **Local-First Safety**: Client data stays local. Workflow scripts run in user-space, avoiding the security risks of public cloud API networks.
* **Self-Healing Features**: Includes built-in error handling and correction fallbacks for handling corrupted OCR scans or missing fields.
* **Manual Checkpoints**: Implements file-based human approvals to safely pause automated runs for compliance checks.

---

## 3. Repository Structure

```
orcha-salesflow/
  ├── README.md                      # Presentation guide and setup
  ├── ORCHA_WORKFLOW_BLUEPRINT.md    # Detail of canvas layout
  ├── ORCHA_NODE_MAP.json            # Machine-readable canvas graph configuration
  ├── index.html                     # Control center dashboard UI
  ├── business_data/                 # Input Catalogues and Templates
  │   ├── inbox/                     # Raw email client files (.txt)
  │   ├── attachments/               # Vendor quote files
  │   ├── crm/                       # CSV CRM database & Catalog rules
  │   └── templates/                 # Markdown templates (proposals, approval requests)
  ├── scripts/                       # Executable Python modules
  │   ├── parse_email.py             # Email body regex parser
  │   ├── extract_quote_fields.py     # OCR-text heuristics processor
  │   ├── lead_scoring.py            # Lead qualification grader
  │   ├── pricing_check.py           # Catalog validator & exceptions checker
  │   ├── generate_proposal.py       # Document compiler
  │   ├── update_crm.py              # Idempotent CSV CRM manager
  │   ├── audit_logger.py            # JSONL compliance logger
  │   ├── server.py                  # Local Dashboard server
  │   └── run_salesflow.py           # Main workflow runtime orchestrator
  ├── applescript/                   # Mac-native AppleScripts (source code)
  │   ├── open_mail_and_search.scpt
  │   ├── create_finder_case_folder.scpt
  │   ├── update_numbers_crm.scpt
  │   ├── create_calendar_followup.scpt
  │   └── open_proposal_for_review.scpt
  ├── output/                        # Compiled workflow results
  │   ├── proposals/                 # Generated proposals / request letters
  │   ├── approvals/                 # Exception review reports
  │   ├── case_folders/              # Local client directories
  │   ├── audit_logs/                # Run-specific audit trails
  │   └── run_reports/               # High-level pipeline reports
  └── docs/                          # Architecture Documentation
      ├── FAILURE_AND_RECOVERY_PATHS.md # Self-healing & exceptions guide
      ├── HUMAN_APPROVAL_DESIGN.md   # Approval checkpoint explanation
      └── SECURITY_AND_NDA_SAFE_DESIGN.md # Local GDPR compliance guide
```

---

## 4. Setup and How to Run

### Ingestion Setup
Place your incoming prospect lead files under `business_data/inbox/` (as `.txt` files) and quote specifications under `business_data/attachments/`.

### Local Dashboard Server
To start the Control Center Dashboard:
```powershell
python scripts/server.py
```
This runs a local HTTP server at `http://localhost:8000`. You can monitor pipeline files, view/decide pricing exception checkpoints, and trigger manual pipeline runs.

### CLI Workflow Run
To execute the pipeline directly from the command line:
```powershell
python scripts/run_salesflow.py
```

---

## 5. Privacy-Safe Design
* **Uses Representative Business Records**: No protected client records are included in the repository.
* **No External API Keys Required**: Runs entirely offline, keeping customer info secure.
* **Local Data Integrity**: Leads, case folders, proposals, and logs are processed locally.
* **Traceable Approvals**: Pricing exceptions require manual resolution before a proposal is compiled.
