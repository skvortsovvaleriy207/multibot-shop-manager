# Update 1: Global DB Sync & Google Sheets Fixes

**Date:** 2026-01-31
**Status:** Completed

## 1. Fixes Applied (`bestsocialbot`, `besthomebot`, `gifthealthbot`, `investmentsbot`, `auto_avia`, `ourwonderfulbot`)

### Sync Logic (Push vs Pull)
- **Problem:** After importing a user from the Global DB, the bots were using `sync_with_google_sheets()` (Pull from Sheets) instead of `sync_db_to_google_sheets()` (Push to Sheets). This caused new users to be overwritten or not appear in the Sheet.
- **Fix:** Switched to `sync_db_to_google_sheets()` immediately after Global DB import in `cmd_start` handler.

### Data Unpacking from Global DB
- **Problem:** The `get_global_user_survey` function returns a flat dictionary of survey data, but the bots were trying to access a nested `survey_data` key. This resulted in empty or incorrect data being saved to the local DB.
- **Fix:** Updated `main.py` in all bots to copy the survey data directly: `user_data_for_db = survey_data.copy()`.

### Google Sheets Initialization
- **Problem:** `init_unified_sheet()` was often missing or not called, meaning sheet headers might not be set up correctly on startup.
- **Fix:** Added `await init_unified_sheet()` to the `main()` function of all bots.

### Auto Avia Specifics
- **Note:** `auto_avia` did not previously have Global DB import logic. It has been added to align with the ecosystem.

## 2. Shared Component Updates (`shared_storage/global_db.py`)

- Added debug logging to `get_global_user_survey` and `save_global_user` to trace data flow.

## 3. Deployment status

- [x] `bestsocialbot`: Updated and verified.
- [x] `besthomebot`: Updated.
- [x] `gifthealthbot`: Updated.
- [x] `investmentsbot`: Updated.
- [x] `auto_avia`: Updated (Added Global DB logic).
- [x] `ourwonderfulbot`: Updated (Fixed sync direction and unpacking).

## 4. Verification Steps

For each bot, the following flow is expected to work:
1. User `/start` (New User).
2. Bot checks Local DB -> Not found.
3. Bot checks Global DB -> Found (if user exists in `ourwonderfulbot` or others).
4. Bot imports data -> Saves to Local DB.
5. Bot pushes to Google Sheet (`sync_db_to_google_sheets`).
6. Bot registers subscription in Global DB.
7. Bot shows Main Menu (Shop/Showcase).

If user is NOT in Global DB:
1. Bot starts Captcha flow.
2. After Captcha -> Save to Local DB.
3. Bot automatically imports from Global DB (if user exists there now?) or eventually syncs.
