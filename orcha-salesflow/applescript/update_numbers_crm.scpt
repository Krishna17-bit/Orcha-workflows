-- =============================================================================
-- ORCHA SALESFLOW - MAC-NATIVE AUTOMATION
-- Script: update_numbers_crm.scpt
-- Purpose: Launches Apple Numbers and updates cells within the Sales Pipeline sheet.
--          Searches for a row with matching lead_id. If found, updates it.
--          Otherwise, appends a new row at the bottom of the table.
--
-- How Orcha Calls This:
--   Orcha executes this script using the Mac CLI runner:
--   osascript applescript/update_numbers_crm.scpt "LEAD-001" "Apex Systems" "115200.00" "Proposal Preparation" "Net 30"
-- =============================================================================

on run argv
    set leadId to "LEAD-000"
    set companyName to "Generic Client"
    set dealValue to "0.00"
    set pipelineStage to "Lead Intake"
    set paymentTerms to "Net 30"
    
    if (count of argv) > 0 then set leadId to item 1 of argv
    if (count of argv) > 1 then set companyName to item 2 of argv
    if (count of argv) > 2 then set dealValue to item 3 of argv
    if (count of argv) > 3 then set pipelineStage to item 4 of argv
    if (count of argv) > 4 then set paymentTerms to item 5 of argv

    log "Updating Apple Numbers sheet with: " & leadId
    
    tell application "Numbers"
        activate
        delay 0.5
        
        -- Open CRM spreadsheet
        -- e.g., set crmFile to posix file "/absolute/path/to/sales_pipeline.csv"
        -- open crmFile
        
        -- Target the front document, active sheet, and first table
        tell document 1
            tell active sheet
                tell table 1
                    set rowCount to count of rows
                    set foundRow to 0
                    
                    -- Search for existing lead_id in Column A (Column 1)
                    repeat with i from 2 to rowCount
                        if value of cell 1 of row i is leadId then
                            set foundRow to i
                            exit repeat
                        end if
                    end repeat
                    
                    if foundRow > 0 then
                        -- Update existing row
                        set value of cell 2 of row foundRow to companyName
                        set value of cell 5 of row foundRow to dealValue
                        set value of cell 6 of row foundRow to pipelineStage
                        set value of cell 8 of row foundRow to paymentTerms
                        log "Updated existing row " & foundRow
                    else
                        -- Append new row
                        add row below row rowCount
                        set newRow to rowCount + 1
                        set value of cell 1 of row newRow to leadId
                        set value of cell 2 of row newRow to companyName
                        set value of cell 5 of row newRow to dealValue
                        set value of cell 6 of row newRow to pipelineStage
                        set value of cell 8 of row newRow to paymentTerms
                        log "Added new row " & newRow
                    end if
                end tell
            end tell
        end tell
    end tell
    
    return "SUCCESS: Apple Numbers CRM sheet updated for lead " & leadId
end run
