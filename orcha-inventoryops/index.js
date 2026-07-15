// OrchaInventoryOps Dashboard Script

document.addEventListener("DOMContentLoaded", () => {
    // Initial fetch
    fetchInventory();
    fetchLedger();
    fetchApprovals();
    checkPaths();

    // Event listeners
    const runBtn = document.getElementById("btn-trigger-run");
    if (runBtn) {
        runBtn.addEventListener("click", triggerWorkflowRun);
    }
    
    const verifyBtn = document.getElementById("btn-verify-connections");
    if (verifyBtn) {
        verifyBtn.addEventListener("click", checkPaths);
    }
    
    const addSkuForm = document.getElementById("add-sku-form");
    if (addSkuForm) {
        addSkuForm.addEventListener("submit", submitNewSKU);
    }
});

// Fetch inventory stocks from local CSV via API
function fetchInventory() {
    fetch("/api/inventory")
        .then(res => res.json())
        .then(data => {
            renderInventoryTable(data);
            const badge = document.getElementById("sku-count-badge");
            if (badge) badge.textContent = `${data.length} SKUs`;
        })
        .catch(err => {
            console.error("Error fetching inventory stock records:", err);
            logConsole("System Error fetching stock catalog data.", "error");
        });
}

// Fetch open purchase orders from ledger CSV via API
function fetchLedger() {
    fetch("/api/ledger")
        .then(res => res.json())
        .then(data => {
            renderLedgerTable(data);
            const badge = document.getElementById("po-count-badge");
            if (badge) badge.textContent = `${data.length} Orders`;
        })
        .catch(err => {
            console.error("Error fetching ledger database records:", err);
            logConsole("System Error fetching ledger database.", "error");
        });
}

// Fetch active approval checkpoints in output/approvals/
function fetchApprovals() {
    fetch("/api/approvals")
        .then(res => res.json())
        .then(data => {
            renderApprovalsList(data);
            const pendingCount = data.filter(item => item.decision === "PENDING").length;
            const badge = document.getElementById("approvals-pending-badge");
            if (badge) {
                badge.textContent = `${pendingCount} Awaiting`;
                if (pendingCount > 0) {
                    badge.className = "badge warning-badge";
                } else {
                    badge.className = "badge";
                }
            }
        })
        .catch(err => {
            console.error("Error fetching approvals data:", err);
        });
}

// Render stock database into Table view
function renderInventoryTable(items) {
    const tbody = document.getElementById("inventory-tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    
    items.sort((a, b) => a.sku.localeCompare(b.sku));
    
    items.forEach(item => {
        const tr = document.createElement("tr");
        
        // Match status class
        let statusClass = "healthy";
        if (item.status === "CRITICAL" || item.status === "STOCKOUT_RISK") {
            statusClass = "critical";
        } else if (item.status === "LOW_STOCK") {
            statusClass = "low_stock";
        }
        
        tr.innerHTML = `
            <td style="font-weight: 700; font-family: var(--font-mono);">${item.sku}</td>
            <td>
                <div style="font-weight: 500;">${item.item_name}</div>
                <div style="font-size: 11px; color: var(--text-muted);">${item.category}</div>
            </td>
            <td>${item.warehouse}</td>
            <td>
                <form class="edit-stock-form" onsubmit="submitStockChange(event, '${item.sku}')">
                    <input type="number" step="any" class="stock-input" value="${item.current_stock}" id="stock-val-${item.sku}">
                    <button type="submit" class="btn-icon" title="Save Inventory Change">
                        <i class="fa-solid fa-check"></i>
                    </button>
                </form>
            </td>
            <td>${item.reorder_threshold} / ${item.target_stock}</td>
            <td>${item.preferred_supplier}</td>
            <td><span class="status-chip ${statusClass}">${item.status}</span></td>
            <td>
                <button class="btn-icon" onclick="triggerImmediateSKUEvaluation('${item.sku}')" title="Re-evaluate Stock">
                    <i class="fa-solid fa-arrows-rotate"></i>
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Render ledger database into Table view
function renderLedgerTable(orders) {
    const tbody = document.getElementById("ledger-tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    
    if (orders.length === 0) {
        tr = document.createElement("tr");
        tr.innerHTML = `<td colspan="8" style="text-align: center; color: var(--text-muted);">No open orders recorded in the ledger database.</td>`;
        tbody.appendChild(tr);
        return;
    }
    
    // Sort orders by last updated date or PO ID descending
    orders.sort((a, b) => b.po_id.localeCompare(a.po_id));
    
    orders.forEach(order => {
        const tr = document.createElement("tr");
        
        let apprClass = "healthy";
        if (order.approval_status === "REJECTED") {
            apprClass = "critical";
        } else if (order.approval_status === "PENDING" || order.approval_status === "REQUEST_MORE_INFO") {
            apprClass = "low_stock";
        }
        
        let statClass = "healthy";
        if (order.po_status === "HOLD") {
            statClass = "low_stock";
        } else if (order.po_status === "CANCELLED") {
            statClass = "critical";
        }
        
        tr.innerHTML = `
            <td style="font-family: var(--font-mono); font-size: 11px;">${order.po_id}</td>
            <td style="font-weight: 600; font-family: var(--font-mono);">${order.sku}</td>
            <td>${order.supplier_name}</td>
            <td>${order.quantity}</td>
            <td style="font-weight: 600;">$${parseFloat(order.total_amount).toFixed(2)}</td>
            <td><span class="status-chip ${apprClass}">${order.approval_status}</span></td>
            <td><span class="status-chip ${statClass}">${order.po_status}</span></td>
            <td style="font-size: 11px; color: var(--text-muted);">${order.last_updated}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Render approvals checklists cards list
function renderApprovalsList(approvals) {
    const container = document.getElementById("approvals-list-container");
    if (!container) return;
    container.innerHTML = "";
    
    if (approvals.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-clipboard-check"></i>
                <p>No active approval requests on this run.</p>
            </div>
        `;
        return;
    }
    
    approvals.sort((a, b) => a.sku.localeCompare(b.sku));
    
    approvals.forEach(app => {
        const div = document.createElement("div");
        div.className = "approval-item";
        
        // Extract basic info from the request text using regex
        let routingReasons = "Compliance routing checklist triggered.";
        const match = app.request_text.match(/## 2\. Policy Violations & Routing Reasons([\s\S]*?)## 3\./);
        if (match && match[1]) {
            routingReasons = match[1].trim();
        }
        
        let totalValue = "N/A";
        const valMatch = app.request_text.match(/\*\*Total Purchase Value:\*\* \$([\d,.]+)/);
        if (valMatch && valMatch[1]) {
            totalValue = `$${valMatch[1]}`;
        }
        
        // Set buttons activation status
        const isApprove = app.decision === "APPROVE" ? "active" : "";
        const isReject = app.decision === "REJECT" ? "active" : "";
        const isInfo = app.decision === "REQUEST_MORE_INFO" ? "active" : "";
        
        div.innerHTML = `
            <div class="approval-meta">
                <span class="sku-tag">${app.sku}</span>
                <span class="badge warning-badge" style="text-transform: uppercase;">${app.decision}</span>
            </div>
            <div class="approval-reason">
                <div style="font-weight: 600; font-size: 12px; margin-bottom: 4px; color: var(--text-primary);">Value: ${totalValue}</div>
                <div style="font-size: 11px; white-space: pre-line;">${routingReasons}</div>
            </div>
            <div class="approval-actions">
                <button class="btn-sm btn-approve ${isApprove}" onclick="submitApprovalDecision('${app.sku}', 'APPROVE')">
                    <i class="fa-solid fa-check"></i> Approve
                </button>
                <button class="btn-sm btn-reject ${isReject}" onclick="submitApprovalDecision('${app.sku}', 'REJECT')">
                    <i class="fa-solid fa-xmark"></i> Reject
                </button>
                <button class="btn-sm btn-info ${isInfo}" onclick="submitApprovalDecision('${app.sku}', 'REQUEST_MORE_INFO')">
                    <i class="fa-solid fa-circle-info"></i> More Info
                </button>
            </div>
        `;
        container.appendChild(div);
    });
}

// Change stock values via POST request
function submitStockChange(event, sku) {
    if (event) event.preventDefault();
    const inputVal = parseFloat(document.getElementById(`stock-val-${sku}`).value);
    
    if (isNaN(inputVal) || inputVal < 0) {
        logConsole(`Error: Stock quantity must be a non-negative number for SKU ${sku}`, "error");
        return;
    }
    
    logConsole(`Saving revised stock values for SKU ${sku} to ${inputVal}...`, "system");
    
    fetch("/api/edit_stock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: jsonBody = JSON.stringify({ sku: sku, current_stock: inputVal })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "SUCCESS") {
            logConsole(`Stock level updated successfully for ${sku}.`, "success");
            fetchInventory();
        } else {
            logConsole(`Error saving stock changes for ${sku}.`, "error");
        }
    })
    .catch(err => {
        console.error("Error editing stock values:", err);
        logConsole("Network Error updating stock values.", "error");
    });
}

// Immediate evaluation trigger for one SKU (simulation helper)
function triggerImmediateSKUEvaluation(sku) {
    logConsole(`Re-evaluating thresholds and requirements for SKU ${sku}...`, "system");
    // Trigger run to refresh everything
    triggerWorkflowRun();
}

// Submit approval decision checklist click
function submitApprovalDecision(sku, decision) {
    logConsole(`Registering approval authorization signature for ${sku} as ${decision}...`, "system");
    
    fetch("/api/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sku: sku, decision: decision })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "SUCCESS") {
            logConsole(`Checkpoint updated. Decision logged as ${decision} for ${sku}.`, "success");
            fetchApprovals();
            // Automatically refresh data
            fetchInventory();
            fetchLedger();
        } else {
            logConsole(`Error writing approval decision for ${sku}.`, "error");
        }
    })
    .catch(err => {
        console.error("Error posting approval choice:", err);
        logConsole("Network Error writing checkpoint signature.", "error");
    });
}

// Run the core workflow
function triggerWorkflowRun() {
    const runBtn = document.getElementById("btn-trigger-run");
    if (runBtn) {
        runBtn.disabled = true;
        runBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Executing Orcha Canvas...`;
    }
    
    logConsole("Initializing Orcha canvas trigger...", "system");
    logConsole("Terminal nodes spawned. Reading spreadsheets...", "normal");
    
    fetch("/api/run", {
        method: "POST"
    })
    .then(res => res.json())
    .then(data => {
        // Output stdout lines to console
        const lines = data.stdout.split("\n");
        lines.forEach(line => {
            if (line.trim()) {
                let type = "normal";
                if (line.includes("SUCCESS") || line.includes("APPROVED") || line.includes("SUCCESSFULLY")) {
                    type = "success";
                } else if (line.includes("WARNING") || line.includes("PENDING") || line.includes("AWAITING")) {
                    type = "warn";
                } else if (line.includes("CRITICAL") || line.includes("ERROR") || line.includes("MISMATCH")) {
                    type = "error";
                } else if (line.startsWith("[NODE]") || line.startsWith("[SKU PROCESS]")) {
                    type = "system";
                }
                logConsole(line, type);
            }
        });
        
        // Refresh grids
        fetchInventory();
        fetchLedger();
        fetchApprovals();
        
        // Update last run time
        const now = new Date();
        const timeStr = now.toLocaleTimeString() + " " + now.toLocaleDateString();
        const runTimeText = document.getElementById("last-run-timestamp");
        if (runTimeText) runTimeText.textContent = `Last run: ${timeStr}`;
        
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.innerHTML = `<i class="fa-solid fa-bolt"></i> Trigger Workflow Execution`;
        }
    })
    .catch(err => {
        console.error("Error executing workflow:", err);
        logConsole("Orcha Engine runtime failure.", "error");
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.innerHTML = `<i class="fa-solid fa-bolt"></i> Trigger Workflow Execution`;
        }
    });
}

// Log message to CLI console
function logConsole(message, type = "normal") {
    const consoleBox = document.getElementById("cli-console");
    if (!consoleBox) return;
    
    const line = document.createElement("div");
    line.className = `console-line ${type}`;
    line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    consoleBox.appendChild(line);
    
    // Auto scroll to bottom
    consoleBox.scrollTop = consoleBox.scrollHeight;
}

// Verify connection paths and update status badges
function checkPaths() {
    logConsole("Verifying local database file connections...", "system");
    fetch("/api/verify_paths")
        .then(res => res.json())
        .then(data => {
            updatePathIndicator("current-stock", data.current_stock.exists, data.current_stock.size_bytes);
            updatePathIndicator("reorder-thresholds", data.reorder_thresholds.exists, data.reorder_thresholds.size_bytes);
            updatePathIndicator("supplier-master", data.supplier_master.exists, data.supplier_master.size_bytes);
            updatePathIndicator("open-purchase-orders", data.open_purchase_orders.exists, data.open_purchase_orders.size_bytes);
            logConsole("Local data connections verified.", "success");
        })
        .catch(err => {
            console.error("Error verifying connections:", err);
            logConsole("Connection verification failed.", "error");
        });
}

function updatePathIndicator(elementId, exists, size) {
    const el = document.getElementById(`status-${elementId}`);
    if (!el) return;
    if (exists) {
        el.className = "path-indicator success";
        el.innerHTML = `<i class="fa-solid fa-circle-check"></i> Connected (${size} B)`;
    } else {
        el.className = "path-indicator error";
        el.innerHTML = `<i class="fa-solid fa-circle-xmark"></i> Disconnected`;
    }
}

// Add a new SKU manually from UI
function submitNewSKU(event) {
    event.preventDefault();
    
    const sku = document.getElementById("new-sku").value.trim();
    const itemName = document.getElementById("new-name").value.trim();
    const category = document.getElementById("new-category").value.trim() || "General";
    const warehouse = document.getElementById("new-warehouse").value.trim() || "Warehouse A";
    const currentStock = parseFloat(document.getElementById("new-stock").value);
    const threshold = parseFloat(document.getElementById("new-threshold").value);
    const target = parseFloat(document.getElementById("new-target").value);
    const supplier = document.getElementById("new-supplier").value;
    const unitCost = parseFloat(document.getElementById("new-unit-cost").value);
    
    logConsole(`Registering new SKU item ${sku} in inventory sheet...`, "system");
    
    fetch("/api/add_sku", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            sku: sku,
            item_name: itemName,
            category: category,
            warehouse: warehouse,
            current_stock: currentStock,
            reorder_threshold: threshold,
            target_stock: target,
            preferred_supplier: supplier,
            unit_cost: unitCost
        })
    })
    .then(res => {
        if (!res.ok) {
            throw new Error("Failed to register new SKU");
        }
        return res.json();
    })
    .then(data => {
        if (data.status === "SUCCESS") {
            logConsole(`Successfully registered SKU ${sku} into databases.`, "success");
            // Reset form
            document.getElementById("add-sku-form").reset();
            // Refresh tables
            fetchInventory();
            checkPaths();
        } else {
            logConsole("Error writing new SKU record.", "error");
        }
    })
    .catch(err => {
        console.error("Error registering SKU:", err);
        logConsole(`Network Error registering new SKU: ${err.message}`, "error");
    });
}

// Export functions to global scope for HTML event handlers
window.logConsole = logConsole;
