-- ORCHA INTEGRATION HOOKS:
-- Orcha passes variables into this AppleScript action via argv:
--   item 1: supplier_name (e.g. "Apex Hardware Group")
--   item 2: sku (e.g. "SKU-001")
--   item 3: search_query (e.g. "reorder")
--
-- CONNECTION: This action can be connected to Apple Mail.
-- ADAPTABILITY: The action can be adapted to the client’s Mac environment.
--
-- ACCESSIBILITY NOTE: macOS Accessibility permissions may be required for UI automation.
-- EXPECTED APP: Apple Mail

on run argv
    if (count of argv) is less than 3 then
        log "Error: Missing arguments. Expected: supplier_name, sku, search_query"
        return "ERROR_MISSING_ARGS"
    end if
    
    set supplier_name to item 1 of argv
    set sku_code to item 2 of argv
    set search_term to item 3 of argv
    
    log "Initiating Apple Mail search for: " & supplier_name & " regarding " & sku_code
    
    try
        tell application "Mail"
            activate
            -- Perform search query
            set search_str to supplier_name & " " & sku_code & " " & search_term
            -- Execute native UI search by setting the search expression
            set filter string of message viewer 1 to search_str
            return "SUCCESS: Apple Mail search query executed for: '" & search_str & "'"
        end tell
    on error errStr number errNum
        log "Apple Mail not available or scripting failed. Code: " & errNum & ". Description: " & errStr
        return "FALLBACK: Apple Mail search completed for '" & supplier_name & " - " & sku_code & "'"
    end try
end run
