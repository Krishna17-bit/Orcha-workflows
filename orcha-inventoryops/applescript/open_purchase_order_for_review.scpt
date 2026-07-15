-- ORCHA INTEGRATION HOOKS:
-- Orcha passes variables into this AppleScript action via argv:
--   item 1: purchase_order_path (e.g. "/path/to/purchase_order_SKU-002.md")
--   item 2: sku (e.g. "SKU-002")
--   item 3: po_id (e.g. "PO-2026-SKU-002-XXXX")
--
-- CONNECTION: This action can be connected to TextEdit or default markdown viewer.
-- ADAPTABILITY: The action can be adapted to the client’s Mac environment.
--
-- ACCESSIBILITY NOTE: macOS Accessibility permissions may be required for UI automation.
-- EXPECTED APP: TextEdit or default markdown viewer

on run argv
    if (count of argv) is less than 3 then
        log "Error: Missing arguments. Expected: purchase_order_path, sku, po_id"
        return "ERROR_MISSING_ARGS"
    end if
    
    set po_path to item 1 of argv
    set sku_code to item 2 of argv
    set po_id to item 3 of argv
    
    log "Review PO hook requested for SKU: " & sku_code & ", PO: " & po_id
    
    try
        set mac_file_path to POSIX file po_path
        
        tell application "TextEdit"
            activate
            open mac_file_path
            return "SUCCESS: TextEdit opened purchase order at '" & po_path & "'"
        end tell
    on error errStr number errNum
        log "TextEdit application scripting failed. Code: " & errNum & ". Description: " & errStr
        return "FALLBACK: Purchase order document '" & po_path & "' is ready for manual dispatch"
    end try
end run
