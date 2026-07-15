# PROCUREMENT APPROVAL REQUEST: {sku}

An inventory or invoice matching exception has triggered this compliance approval routing. Downstream automation is paused pending decision.

## 1. Request Details
- **SKU:** {sku}
- **Item Name:** {item_name}
- **Category:** {category}
- **Warehouse:** {warehouse}
- **Preferred Supplier:** {supplier_name}
- **Reorder Quantity:** {quantity}
- **Unit Cost:** ${unit_cost:,.2f}
- **Total Purchase Value:** ${total_value:,.2f}

## 2. Policy Violations & Routing Reasons
{routing_reasons}

## 3. Recommended Action
- **Urgency Level:** {urgency}
- **Proposed Decision:** {proposed_decision}
- **Resolution Recommendation:** {recommendation_text}

## 4. Human Decision Checkpoint
To process this request, please edit or create the approval decision file in the approvals folder:
`output/approvals/approval_decision_{sku}.txt`

**Valid Decision Options (Type exactly as shown):**
- `APPROVE`
- `REJECT`
- `REQUEST_MORE_INFO`

*Workflow run audit ID: {run_id}*
