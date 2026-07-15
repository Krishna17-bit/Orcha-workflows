# Orcha Workflows Collection

Welcome to the **Orcha Workflows** repository. This collection contains production-ready, local-first automation templates designed for the **Orcha Canvas** visual scripting environment. 

These workflows showcase how standard scripting modules (Python, terminal tasks) and macOS desktop integrations (AppleScript wrappers for Finder, Numbers, Mail, Calendar, and TextEdit) coordinate seamlessly to automate complex, human-in-the-loop business operations.

---

## Workflows Included

This repository contains the following automation pipelines:

### 1. [OrchaInventoryOps](./orcha-inventoryops)
A workflow template for inventory replenishment and supplier procurement tracking.
* **Intake**: Ingests stock levels and supplier pricing catalog rows from local spreadsheet ledgers.
* **Extraction & Matching**: Scans incoming supplier invoice updates, matching prices and items against catalogs to flag discrepancy warnings.
* **Compliance Approval Checkpoint**: Pauses execution on order cost limits or supplier reliability drops, generating compliance reviews for manager approval.
* **Native Desktop Integrations**: Generates approved purchase orders, updates inventory ledgers in Apple Numbers, maps Finder workspaces, and schedules supplier followup dates in Apple Calendar.

### 2. [OrchaSalesFlow](./orcha-salesflow)
A workflow template for B2B sales intake, lead qualification scoring, and proposal compilation.
* **Intake**: Watches mail client folder queues for incoming text-based lead requests.
* **Extraction**: Uses OCR parsing filters to scan incoming quote specifications.
* **Scoring & Verification**: Runs lead qualification algorithms to segment Hot/Warm prospects and checks deal terms against catalog policy catalogs.
* **Human Safeguards Checkpoint**: Pauses execution on custom discounts or non-standard payment terms to request manual manager approval.
* **Native Desktop Integrations**: Compiles watermarked client proposals, creates Finder client case directories, updates pipeline stages in local CSV trackers, and registers calendar reminders.

---

## Design Principles

* **Local-First & Privacy-Safe**: All workflows run in user-space using mock privacy-safe business records. No external API keys or cloud database connections are required, keeping corporate data secure.
* **Asynchronous Checkpoints**: Long-running approval exceptions generate structured Markdown reviews and await decision files (`approval_decision_*.txt`) to proceed, preventing background run hangs.
* **Self-Healing Fallbacks**: Scripts include built-in recovery routines, such as spelling correction overrides for low-confidence OCR text extraction.
* **Comprehensive Audit Compliance**: Every pipeline run emits structured JSONL audit trails and formatted run report summaries.
