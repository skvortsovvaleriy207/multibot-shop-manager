# Update 2: Stabilization of Synchronization and Automarket

**Date:** 2026-01-31
**Status:** Completed
**Focus:** `bestsocialbot` (Google Sheets, Daily Scheduler, Automarket)

## 1. Modified Files
The following files were updated to improve stability and reliability:
- `bestsocialbot/google_sheets.py`
- `bestsocialbot/daily_scheduler.py`
- `bestsocialbot/automarket_sheets.py`
- `bestsocialbot/survey.py`

## 2. Key Changes & Fixes

### A. Google Sheets Stabilization (`google_sheets.py`)
- **Rate Limiting:** Added a `@retry_google_api(retries=5, delay=5)` decorator to all critical Google Sheets interactions. This ensures that temporary API errors (429, 500) do not crash the bot.
- **Data Safety (Critical):** Implemented a "Pre-Sync" check in `sync_db_to_google_sheets()`. Before pushing local DB data to Google Sheets, the bot now attempts to fetch the latest data from the sheet. If this fetch fails, the export is aborted to prevent overwriting correct data with stale or empty data.
- **Unified Storage:** Standardized usage of `MAIN_SURVEY_SHEET_URL` (aliased as `UNIFIED_SHEET_URL`) to ensure all bots write to the central "Основная таблица".

### B. Daily Scheduler (`daily_scheduler.py`)
- **Strict Timing:** Implemented logic to trigger synchronization exactly at **17:00 MSK**, as per the Technical Task (TZ No. 2).
- **Sequential Execution:** Tasks are now executed strictly sequentially to avoid overloading the database or the Google API:
    1.  `sync_db_to_google_sheets()` (Main User Data)
    2.  `export_all_automarket_data()` (Products/Services/Orders)
    3.  `export_all_partner_data()` (Partners)
    4.  `update_referral_system()`
    5.  `update_activity_system()`
    6.  `generate_statistics()`

### C. Automarket Integration (`automarket_sheets.py`)
- **Quota Management:** Replaced `asyncio.gather` (parallel execution) with sequential execution in `export_all_automarket_data()`. This significantly reduces the "Read requests per minute" quota usage during startup and daily sync.
- **Full Sync Support:** Verified and updated functions for syncing:
    - Products (`sync_products_to_sheet`, `sync_products_from_sheet`)
    - Services (`sync_services_to_sheet`, `sync_services_from_sheet`)
    - Orders (`sync_orders_to_sheet`, `sync_orders_from_sheet`)

### D. User Registration Flow (`survey.py`)
- **Global DB Check:** Confirmed integration of `import_global_user` at the start of the survey (`start_survey` handler). The bot now checks if the user exists in the Global DB to skip the survey if possible.
- **Post-Survey Sync:** Explicitly triggers `sync_db_to_google_sheets()` immediately after a user completes the survey.

## 3. Verification results
- [x] **API Stability:** 429 Errors should be significantly reduced due to serialized execution and retries.
- [x] **Data Integrity:** The risk of overwriting Google Sheets data with empty local data is minimized by the pre-sync check.
- [x] **Schedule:** The bot is configured to perform its heavy lifting at 17:00 MSK daily.
