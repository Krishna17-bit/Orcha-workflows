-- =============================================================================
-- ORCHA SALESFLOW - MAC-NATIVE AUTOMATION
-- Script: create_finder_case_folder.scpt
-- Purpose: Automates macOS Finder to create structured client case folders.
--          Creates a folder tree: /CaseFolders/[lead_id]_[company_name]/
--          with subdirectories: Proposals, Communications, and SourceData.
--
-- How Orcha Calls This:
--   Orcha executes this script using the Mac CLI runner:
--   osascript applescript/create_finder_case_folder.scpt "LEAD-001" "Apex_Systems"
-- =============================================================================

on run argv
    set leadId to "LEAD-000"
    set companyName to "Generic_Client"
    
    if (count of argv) > 0 then
        set leadId to item 1 of argv
    end if
    if (count of argv) > 1 then
        set companyName to item 2 of argv
    end if
    
    -- Format folder name safely
    set folderName to leadId & "_" & companyName
    
    tell application "Finder"
        -- Get path to user's Documents folder
        set docsPath to path to documents folder as text
        set baseFolderName to "OrchaSalesFlow"
        set casesFolderName to "CaseFolders"
        
        -- 1. Create main project folder under Documents if missing
        set baseDir to docsPath & baseFolderName & ":"
        if not (exists folder baseDir) then
            make new folder at folder docsPath with properties {name:baseFolderName}
        end if
        
        -- 2. Create CaseFolders index folder if missing
        set casesDir to baseDir & casesFolderName & ":"
        if not (exists folder casesDir) then
            make new folder at folder baseDir with properties {name:casesFolderName}
        end if
        
        -- 3. Create specific client case folder
        set clientDir to casesDir & folderName & ":"
        if not (exists folder clientDir) then
            set newClientFolder to make new folder at folder casesDir with properties {name:folderName}
            
            -- Initialize subdirectories for organized record-keeping
            make new folder at folder clientDir with properties {name:"Proposals"}
            make new folder at folder clientDir with properties {name:"Communications"}
            make new folder at folder clientDir with properties {name:"SourceData"}
        end if
        
        -- Open Finder and highlight the client folder
        reveal folder clientDir
        activate
    end tell
    
    return "SUCCESS: Finder case folder created and focused: ~/Documents/" & baseFolderName & "/" & casesFolderName & "/" & folderName
end run
