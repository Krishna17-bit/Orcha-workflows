# OrchaInventoryOps — Mac-Native Inventory & Procurement Automation

This repository provides a local-first automation workflow template designed for stock evaluation, supplier update ingestion, OCR-style document extraction, compliance approval checkpoints, and native macOS integrations.

---

## 1. What This Workflow Does
The system automates the inventory replenishment lifecycle:
1. **Intake:** Ingests inventory records and reorder limits from local CSV spreadsheets.
2. **Supplier Communication Parsing:** Scans local directories for incoming updates on supplier availability, price adjustments, or delivery delays.
3. **Billing Document Check:** Extracts fields from invoice text and checks them against expected pricing catalog data, flagging price variances.
4. **Replenishment Recommendations:** Evaluates days of stock remaining and determines target reorder quantities.
5. **Compliance Authorization Gates:** Evaluates order size, value, and invoice checks against policy rules. Pauses execution for exceptions to await manual operator sign-off.
6. **Mac-Native UI Integrations:** Once approved, compiles purchase orders, updates Numbers-compatible ledgers, opens Finder case workspaces, displays order previews in TextEdit, and schedules calendar appointments.
7. **Comprehensive Audit Logs:** Generates structured event logs (JSONL) and detailed run reports (Markdown) to ensure full operational transparency.

---

## 2. System Architecture
The architecture mimics a visual workflow orchestrator containing scheduled triggers, terminal script nodes, conditional logic, and native desktop integration hooks:
* **Visual Blueprint Mapping:** Defined in [ORCHA_WORKFLOW_BLUEPRINT.md](ORCHA_WORKFLOW_BLUEPRINT.md) and mapped systematically via [ORCHA_NODE_MAP.json](ORCHA_NODE_MAP.json).
* **Mac-Native Hooking:** Integrates with local macOS apps (Apple Mail, Finder, Calendar, Numbers) without needing external API keys.
* **Resilient Failure Sourcing:** Implements robust fallbacks for low-confidence OCR scans, supplier pricing variations, and delivery delays.
* **Manual Checkpoints:** Implements file-based human approvals to safely pause automated runs for compliance checks.
* **Audit Trails:** Provides structured audit logs and run reports.

---

## 3. Repository Structure
```
orcha-inventoryops/
  README.md
  ORCHA_WORKFLOW_BLUEPRINT.md
  ORCHA_NODE_MAP.json
  business_data/
    inventory/
      current_stock.csv
      reorder_thresholds.csv
      warehouse_locations.csv
    suppliers/
      supplier_master.csv
      supplier_updates/
    procurement/
      open_purchase_orders.csv
      purchase_approval_rules.csv
      invoice_matching_rules.csv
    documents/
    templates/
      purchase_order_template.md
      approval_request_template.md
      supplier_followup_template.md
      stockout_alert_template.md
  scripts/
    ingest_inventory.py
    parse_supplier_update.py
    extract_invoice_fields.py
    stock_reorder_engine.py
    supplier_selection.py
    invoice_match_check.py
    approval_router.py
    generate_purchase_order.py
    update_inventory_tracker.py
    generate_supplier_followup.py
    audit_logger.py
    run_inventoryops.py
    server.py
  applescript/
    open_mail_supplier_search.scpt
    create_finder_procurement_folder.scpt
    update_numbers_inventory_tracker.scpt
    create_calendar_supplier_followup.scpt
    open_purchase_order_for_review.scpt
  output/
    purchase_orders/
    approvals/
    supplier_followups/
    stockout_alerts/
    case_folders/
    audit_logs/
    run_reports/
  docs/
    FAILURE_AND_RECOVERY_PATHS.md
    HUMAN_APPROVAL_DESIGN.md
    SECURITY_AND_NDA_SAFE_DESIGN.md
    TECHNICAL_DEPTH_NOTES.md
```

---

## 4. Setup and How to Run

### Ingestion Setup
Place your inventory data into the following CSV spreadsheets under `business_data/`:
1. `inventory/current_stock.csv` (active stocks list)
2. `inventory/reorder_thresholds.csv` (reorder rules and approvals configuration)
3. `suppliers/supplier_master.csv` (supplier catalog of record)
4. `procurement/open_purchase_orders.csv` (reorder log ledger)

### Local Dashboard Server
To start the Control Center Dashboard:
```powershell
python scripts/server.py
```
This runs a local HTTP server at `http://localhost:8000`. You can monitor stock levels, view pending approvals, verify data path connectivity, register new SKUs, and trigger workflow runs from this dashboard.

### CLI Workflow Run
To execute the pipeline directly from the command line:
```powershell
python scripts/run_inventoryops.py
```

---

## 5. Security & Deployment Model
* **Local Security Perimeter:** Runs fully offline with local-first file execution. Safe to deploy behind secure corporate networks or isolated sandboxes.
* **Production Adaptability:** 
  1. **Directory Syncing:** Bind active watcher services or network shares to `business_data/documents/` to automate intake of vendor invoices.
  2. **Mail Filters:** Set mail client rules to output supplier messages directly to `supplier_updates/` directory.
  3. **Database Hooking:** Replace CSV ingestion logic with direct database query execution (e.g. SQLite, PostgreSQL, ERP API endpoints).
