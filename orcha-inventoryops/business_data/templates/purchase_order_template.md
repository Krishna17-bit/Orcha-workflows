# PURCHASE ORDER: {po_id}

**Date Generated:** {created_at}  
**Status:** {po_status}  
**Urgency Level:** {urgency}  

## 1. Vendor Details
- **Supplier ID:** {supplier_id}
- **Supplier Name:** {supplier_name}
- **Contact:** {supplier_contact}
- **Email:** {supplier_email}

## 2. Delivery & Destination
- **Warehouse ID:** {warehouse_id}
- **Warehouse Name:** {warehouse_name}
- **Destination Address:** {warehouse_city}
- **Warehouse Manager:** {warehouse_manager} ({warehouse_manager_email})
- **Expected Delivery Date:** {expected_delivery_date}

## 3. Order Items
| SKU | Item Description | Quantity | Unit Price | Total Amount |
| :--- | :--- | :---: | :---: | :---: |
| {sku} | {item_name} | {quantity} | ${unit_price:,.2f} | ${total_amount:,.2f} |

**Total Order Value:** ${total_amount:,.2f}  
**Payment Terms:** {payment_terms}  

## 4. Compliance & Approvals
- **Approval Checkpoint Requirement:** {approval_required}
- **Approval Status:** {approval_status}
- **Approver Role:** {approver_role}
- **Audit ID Link:** {audit_id}

## 5. Operations & Logistics Notes
{operational_notes}

---
*This is an electronically generated purchase order from the local-first OrchaInventoryOps automation workflow.*
