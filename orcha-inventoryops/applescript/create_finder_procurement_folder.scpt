-- ORCHA INTEGRATION HOOKS:
-- Orcha passes variables into this AppleScript action via argv:
--   item 1: sku (e.g. "SKU-002")
--   item 2: po_id (e.g. "PO-2026-SKU-002-XXXX")
--   item 3: supplier_name (e.g. "Apex Hardware Group")
--   item 4: output_path (e.g. "/absolute/path/to/output/case_folders/case_SKU-002")
--
-- CONNECTION: This action can be connected to macOS Finder.
-- ADAPTABILITY: The action can be adapted to the client’s Mac environment.
--
-- ACCESSIBILITY NOTE: macOS Accessibility permissions may be required for UI automation.
-- EXPECTED APP: macOS Finder

on run argv
    if (count of argv) is less than 4 then
        log "Error: Missing arguments. Expected: sku, po_id, supplier_name, output_path"
        return "ERROR_MISSING_ARGS"
    end if
    
    set sku_code to item 1 of argv
    set po_id to item 2 of argv
    set supplier_name to item 3 of argv
    set target_folder_path to item 4 of argv
    
    log "Creating Finder folder for SKU: " & sku_code & ", PO: " & po_id
    
    try
        -- Convert POSIX path to alias for Finder
        set posix_path to target_folder_path
        
        tell application "Finder"
            if not (exists POSIX file posix_path as alias) then
                -- Fallback to terminal creation
                do shell script "mkdir -p " & quoted form of posix_path
            end if
            
            -- Open the folder in Finder window to focus attention
            set target_folder to POSIX file posix_path as alias
            reveal target_folder
            activate
            
            return "SUCCESS: Finder folder opened at '" & posix_path & "'"
        end tell
    on error errStr number errNum
        log "Finder scripting not available. Code: " & errNum & ". Description: " & errStr
        return "FALLBACK: Directory created at '" & target_folder_path & "' via command line"
    end try
end run
