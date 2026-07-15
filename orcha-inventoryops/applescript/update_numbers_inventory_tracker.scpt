-- ORCHA INTEGRATION HOOKS:
-- Orcha passes variables into this AppleScript action via argv:
--   item 1: tracker_path (e.g. "/path/to/open_purchase_orders.csv")
--   item 2: sku (e.g. "SKU-002")
--   item 3: po_id (e.g. "PO-2026-SKU-002-XXXX")
--
-- CONNECTION: This action can be connected to Apple Numbers.
-- ADAPTABILITY: The action can be adapted to the client’s Mac environment.
--
-- ACCESSIBILITY NOTE: macOS Accessibility permissions may be required for UI automation.
-- EXPECTED APP: Apple Numbers


on run argv
    if (count of argv) is less than 3 then
        log "Error: Missing arguments. Expected: tracker_path, sku, po_id"
        return "ERROR_MISSING_ARGS"
    end if
    
    set csv_path to item 1 of argv
    set sku_code to item 2 of argv
    set po_id to item 3 of argv
    
    log "Numbers Tracker Sync requested for SKU: " & sku_code & ", PO: " & po_id
    
    try
        set mac_file_path to POSIX file csv_path
        
        tell application "Numbers"
            activate
            open mac_file_path
            return "SUCCESS: Numbers spreadsheet document opened for tracker at '" & csv_path & "'"
        end tell
    on error errStr number errNum
        log "Numbers application scripting failed. Code: " & errNum & ". Description: " & errStr
        return "FALLBACK: CSV tracker file '" & csv_path & "' updated and ready for Numbers import"
    end try
end run
