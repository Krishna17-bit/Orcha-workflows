# Pricing Exception Approval Request

**Lead ID:** {{lead_id}}  
**Company:** {{company_name}}  
**Contact:** {{contact_name}} ({{email}})  
**Urgency:** {{urgency}}  

---

## Exception Summary
This lead has triggered pricing exceptions that require senior manager review before a proposal can be generated.

### Risk Flags
{{risk_flags}}

### Financial Details
- **Service Requested:** {{service_name}}
- **Standard Base Price:** ${{base_price}}
- **Delivery Surcharge:** ${{surcharge}}
- **Requested Discount:** {{requested_discount}}% (Allowed limit: {{max_allowed_discount}}%)
- **Proposed Deal Value:** ${{proposed_deal_value}}
- **Payment Terms:** {{payment_terms}}

---

## Recommended Action
{{recommended_action}}

## Decision Checkpoint
To resolve this checkpoint, create a file named `approval_decision.txt` in the same directory containing exactly one of the following decisions on the first line:
- **APPROVE**
- **REJECT**
- **REQUEST_MORE_INFO**

*Note: The Orcha workspace runner checks for the presence of this decision file to resume the execution pipeline.*
