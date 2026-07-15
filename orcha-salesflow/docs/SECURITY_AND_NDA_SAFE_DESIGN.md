# Security and Privacy-Safe Workflow Design

This document details the security safeguards and privacy-safe design features of the **OrchaSalesFlow** workflow implementation.

---

## 1. Local-First Execution
The workflow operates entirely on the local macOS desktop using standard command line tools and scripting bridges.
* **Local File Processing**: Intake files, quote attachments, proposals, and logs are processed locally.
* **Native Desktop Bridges**: AppleScript bridges interact with Finder, Apple Mail, Numbers, and Calendar directly on the Mac, avoiding network exposure.
* **Data Containment**: Customer data is kept on the client's local machine, satisfying strict compliance frameworks.

---

## 2. No External API Key Requirement
Unlike cloud automation software that requires exposing internal systems via web API keys, this workflow runs completely offline.
* **Offline Processing**: Avoids dependency on external CRM APIs, email service providers, or cloud AI services.
* **Reduced Vulnerability**: Eliminates risks associated with exposed access tokens, database credentials, or third-party cloud data leaks.

---

## 3. Protected Data Handling
To ensure confidentiality during presentations and compliance reviews:
* **Representative Business Records**: The project contains only fictional, representative business records (e.g. Apex Systems, Spark Creative). No actual client records or protected personal data are stored in the repository.
* **GDPR Compliance**: The design illustrates data isolation. If adapted to real production pipelines, personal data remains within the local network.

---

## 4. Human Approval for Risky Decisions
High-risk financial operations are protected by manual review checkpoints:
* **Exceptions Checks**: The checker flags discount rates > 15%, low budget metrics, or non-standard payment terms.
* **Checkpoint Suspensions**: Suspends running threads, preventing automated generation of unauthorized contracts until a manager signs off.

---

## 5. Auditability and Compliance Trails
To satisfy security audits:
* **JSONL Audit Trails**: Every logic transition, execution status, input, output, and retry event is recorded in a local log file inside `output/audit_logs/`.
* **Traceable Decisions**: Approvals are tracked, linking the manager's sign-off file to the compiled proposal and CRM spreadsheet modifications.

---

## 6. Adaptation to Client Environment
This workflow implementation is designed to easily map onto production client systems:
* **Intake Rules**: Connect the intake node directly to Apple Mail rules or local watch folders.
* **Numbers/Excel Integration**: Sync data with spreadsheet CRM tables or internal databases.
* **Canvas Execution**: Ingest the configuration schema directly into Orcha canvas engines to coordinate native processes securely.
