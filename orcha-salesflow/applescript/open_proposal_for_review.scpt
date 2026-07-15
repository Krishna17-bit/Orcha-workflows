-- =============================================================================
-- ORCHA SALESFLOW - MAC-NATIVE AUTOMATION
-- Script: open_proposal_for_review.scpt
-- Purpose: Opens a generated proposal markdown file in the user's default editor,
--          TextEdit, or Markdown Preview tool for manual review.
--
-- How Orcha Calls This:
--   Orcha executes this script using the Mac CLI runner:
--   osascript applescript/open_proposal_for_review.scpt "/absolute/path/to/proposal_LEAD-001.md"
-- =============================================================================

on run argv
    set proposalPath to ""
    if (count of argv) > 0 then
        set proposalPath to item 1 of argv
    end if
    
    if proposalPath is "" then
        return "ERROR: No proposal file path provided"
    end if
    
    tell application "Finder"
        try
            -- Convert Unix POSIX path to AppleScript file reference
            set macFile to posix file proposalPath
            open macFile
            activate
        on error errStr
            return "ERROR: Failed to open proposal path: " & errStr
        end try
    end tell
    
    return "SUCCESS: Opened proposal for review: " & proposalPath
end run
