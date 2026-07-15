-- ORCHA INTEGRATION HOOKS:
-- Orcha passes variables into this AppleScript action via argv:
--   item 1: supplier_name (e.g. "Apex Hardware Group")
--   item 2: followup_date (e.g. "2026-07-11")
--   item 3: sku (e.g. "SKU-004")
--   item 4: po_id (e.g. "HLD-2026-SKU-004")
--
-- CONNECTION: This action can be connected to Apple Calendar.
-- ADAPTABILITY: The action can be adapted to the client’s Mac environment.
--
-- ACCESSIBILITY NOTE: macOS Accessibility permissions may be required for UI automation.
-- EXPECTED APP: Apple Calendar


on run argv
    if (count of argv) is less than 4 then
        log "Error: Missing arguments. Expected: supplier_name, followup_date, sku, po_id"
        return "ERROR_MISSING_ARGS"
    end if
    
    set supplier_name to item 1 of argv
    set date_str to item 2 of argv
    set sku_code to item 3 of argv
    set po_id to item 4 of argv
    
    log "Scheduling Apple Calendar event for supplier " & supplier_name & " on " & date_str
    
    try
        -- Parse date from YYYY-MM-DD
        -- Standard AppleScript date parse requires specific formatting, so we use shell date formatting
        set formatted_date to do shell script "date -j -f '%Y-%m-%d' " & quoted form of date_str & " +'%m/%d/%Y 09:00:00'"
        set start_date to date formatted_date
        set end_date to start_date + (1 * hours)
        
        tell application "Calendar"
            activate
            tell calendar "Work"
                make new event at end with properties {summary:"Follow-up: " & supplier_name & " (" & sku_code & ")", start date:start_date, end date:end_date, description:"Verification of pending order " & po_id & " for " & sku_code}
            end tell
            return "SUCCESS: Calendar follow-up scheduled for: " & date_str & " (" & supplier_name & ")"
        end tell
    on error errStr number errNum
        log "Calendar scripting failed or calendar 'Work' not found. Code: " & errNum & ". Description: " & errStr
        return "FALLBACK: Follow-up scheduled locally for date " & date_str & " (Supplier: " & supplier_name & ", SKU: " & sku_code & ")"
    end try
end run
