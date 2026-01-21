# Logic for Transferring Changes from Main Google Sheet to Personal Profiles

This document describes the logic for synchronizing user data from a "Main Google Sheet" to the bot's internal database and notifying users of updates to their profiles. This logic is derived from the `auto-avia` bot.

## 1. Overview

The system works by periodically reading a master Google Sheet containing user data. It compares this data with the local SQLite database. If changes are detected for a user (e.g., balance update, new status, changed contact info), the local database is updated, and the user receives a notification in the bot with their new profile details.

## 2. Prerequisites

*   **Libraries**: `gspread` (for Google Sheets), `aiosqlite` (for async SQLite), `aiogram` (for the bot).
*   **Credentials**: A Google Service Account JSON key file (`credentials.json`) must be present and have access to the Google Sheet.
*   **Configuration**: The Google Sheet URL must be defined in `config.py` as `MAIN_SURVEY_SHEET_URL` (or `UNIFIED_SHEET_URL`).

## 3. Database Schema

The `users` table in SQLite serves as the "Personal Profile" storage. It must contain columns that map to the Google Sheet headers.

**Example Schema (`users` table):**
```sql
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    birth_date TEXT,
    location TEXT,
    email TEXT,
    phone TEXT,
    employment TEXT,
    financial_problem TEXT,
    social_problem TEXT,
    ecological_problem TEXT,
    passive_subscriber TEXT,
    active_partner TEXT,
    investor_trader TEXT,
    business_proposal TEXT,
    bonus_total REAL,
    current_balance REAL,
    problem_cost TEXT,
    notes TEXT,
    account_status TEXT,
    updated_at TEXT,
    has_completed_survey INTEGER
    -- Add other columns as needed
);
```

## 4. Implementation Logic

### Step A: Synchronization Function (`sync_with_google_sheets`)

This function resides in `google_sheets.py`. Its job is to:
1.  Connect to the Google Sheet.
2.  Read all records.
3.  Iterate through each row.
4.  Compare the Sheet data with the existing DB data for that `user_id`.
5.  If differences exist:
    *   Update the DB.
    *   Record the change in a dictionary.
6.  Return the dictionary of changes.

**Key Code Snippet (Python):**

```python
async def sync_with_google_sheets():
    try:
        client = gspread.service_account(filename=CREDENTIALS_FILE)
        spreadsheet = client.open_by_url(UNIFIED_SHEET_URL)
        sheet = spreadsheet.worksheet("Основная таблица") # Target specific sheet
        gsheet_data = sheet.get_all_records()
        
        async with aiosqlite.connect("bot_database.db") as db:
            changes = defaultdict(dict)
            
            for row in gsheet_data:
                # 1. Identify User
                user_id_raw = row.get('Telegram ID') or row.get('User ID')
                if not user_id_raw: continue
                user_id = int(user_id_raw)
                
                # 2. Fetch current DB state
                cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                db_user = await cursor.fetchone()
                
                # ... Map DB fields to Sheet columns ...
                # db_fields = { ... }
                # gsheet_fields = { ... }
                
                # 3. Detect Changes
                # for field in gsheet_fields:
                #    if str(db_fields[field]) != str(gsheet_fields[field]):
                #        changes[user_id][field] = {'old': ..., 'new': ...}
                
                # 4. Update Database
                # construct INSERT OR REPLACE query...
                # await db.execute(...)
                
            await db.commit()
            return changes
            
    except Exception as e:
        logging.error(f"Sync error: {e}")
        return None
```

### Step B: Notification Function (`send_user_notification`)

This function resides in `main.py` (or a message handler module). It formats and sends the profile update.

**Key Code Snippet:**

```python
async def send_user_notification(bot: Bot, user_id: int, changes: dict):
    # Fetch latest data from DB to ensure consistency
    async with aiosqlite.connect("bot_database.db") as db:
        cursor = await db.execute("SELECT ... FROM users WHERE user_id = ?", (user_id,))
        user_data = await cursor.fetchone()

    if not user_data: return

    # Format the message
    message = "🔔 Ваш профиль был обновлен. Текущие данные:\n\n"
    # Map DB columns to readable labels
    field_names = {'financial_problem': 'Финансовая проблема', 'current_balance': 'Текущий баланс', ...}
    
    for field, label in field_names.items():
        # Retrieve value from user_dataTuple based on index or dict key
        value = ... 
        message += f"▪️ {label}: {value}\n"

    # Send
    try:
        await bot.send_message(user_id, message)
    except Exception as e:
        logging.error(f"Failed to notify {user_id}: {e}")
```

### Step C: Integration in Main Loop

In `main.py`, the sync is triggered (e.g., on startup or by a scheduler), and the result is used to trigger notifications.

**Key Code Snippet:**

```python
# In main() or specific command handler:
print("[SYNC] Loading changes from Google Sheets...")
changes = await sync_with_google_sheets()

if changes:
    print(f"[OK] Loaded changes for {len(changes)} users")
    for user_id, user_changes in changes.items():
        if user_changes:
            # Notify the user (their "personal profile" view is effectively updated by the DB update, 
            # and this message informs them of the specific changes)
            await send_user_notification(bot, user_id, user_changes)
```

## 5. Summary of Flow

1.  **Admin** updates the **Main Google Sheet** (e.g., adds a bonus, changes a status).
2.  **Bot** runs `sync_with_google_sheets`.
3.  **Bot** detects the difference between the Sheet and the local SQLite DB.
4.  **Bot** updates the **local DB** (`users` table).
5.  **Bot** returns a list of changed user IDs.
6.  **Bot** sends a **Telegram Notification** to each affected user with their updated profile data.
