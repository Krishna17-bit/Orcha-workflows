-- =============================================================================
-- ORCHA SALESFLOW - MAC-NATIVE AUTOMATION
-- Script: open_mail_and_search.scpt
-- Purpose: Launches Apple Mail, focuses the window, and runs a search for the
--          specific contact email to retrieve thread context.
--
-- How Orcha Calls This:
--   Orcha executes this script using the Mac CLI runner:
--   osascript applescript/open_mail_and_search.scpt "sarah.j@apexsystems.com"
-- =============================================================================

on run argv
    -- Orcha dynamically passes the search email as the first argument
    set searchEmail to "sales@orchab2bservices.com"
    if (count of argv) > 0 then
        set searchEmail to item 1 of argv
    end if
    
    log "Initiating Apple Mail search for: " & searchEmail
    
    tell application "Mail"
        activate
        delay 0.5
        
        -- Open a new viewer window if none exist
        if (count of message viewers) is 0 then
            make new message viewer
        end if
        
        -- Set search filter inside active mail viewer
        tell message viewer 1
            set search string to searchEmail
        end tell
    end tell
    
    return "SUCCESS: Apple Mail search query executed for " & searchEmail
end run
