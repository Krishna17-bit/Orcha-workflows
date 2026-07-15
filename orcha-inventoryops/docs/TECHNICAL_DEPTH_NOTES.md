# Technical Depth Notes — OrchaInventoryOps

This workflow uses representative business records so the architecture, routing logic, approval model, and Mac-native automation pattern can be reviewed without exposing protected client information.

## 1. Workflow Architecture

The workflow is structured as a node-based orchestration pipeline rather than a single script. Each business step is isolated into a dedicated processing node, making the workflow easier to debug, extend, and map onto an Orcha canvas.

## 2. Deterministic and Reasoning-Based Logic

The workflow combines deterministic business rules with reasoning-style routing:
- Reorder thresholds
- Stockout risk calculation
- Supplier lead-time comparison
- Invoice price tolerance
- Purchase approval thresholds
- Supplier delay handling
- Approval outcome routing

## 3. Recovery and Fallback Paths

The workflow includes explicit recovery paths for:
- missing inventory values
- missing supplier records
- low-confidence document extraction
- supplier delays
- price mismatch
- approval rejection
- approval requests for more information
- duplicate purchase orders
- partial execution failure

## 4. Local-First Mac Automation

The implementation uses local files, AppleScript hooks, Finder folders, Apple Mail search actions, Calendar follow-ups, and Numbers-compatible CSV trackers. This aligns with Mac-native workflow automation where internal tools may not expose clean APIs.

## 5. Auditability

Every major step emits an execution audit event with:
- run identifier
- SKU
- node name
- status
- input summary
- output summary
- retry count
- approval status
- workflow state

This makes the workflow easier to inspect, debug, and adapt to stricter operational environments.

## 6. Extensibility

The workflow can be extended to support:
- actual Apple Mail rules
- real Numbers or Excel workbooks
- supplier-specific procurement folders
- PDF OCR engines
- approval notifications
- Slack or email approval messages
- ERP/CRM integration where APIs are available
- scheduled execution through Orcha triggers
