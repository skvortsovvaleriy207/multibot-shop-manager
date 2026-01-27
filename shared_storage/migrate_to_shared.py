
import sqlite3
import os
import glob
import time

# Configuration
PROJECT_ROOT = "/home/skvortsovvaleriy207/Proect/Python/multibot-shop-manager"
SHARED_DB_PATH = os.path.join(PROJECT_ROOT, "shared_storage", "multibot_users.db")

# List of bot directories to migrate
BOT_DIRS = [
    os.path.join(PROJECT_ROOT, "bestsocialbot"),
    os.path.join(PROJECT_ROOT, "bestsocialbot_1"),
    os.path.join(PROJECT_ROOT, "investmentsbot")
]

def init_shared_db():
    print(f"Initializing shared database at {SHARED_DB_PATH}...")
    conn = sqlite3.connect(SHARED_DB_PATH)
    cursor = conn.cursor()
    
    # 1. USERS Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            has_completed_survey INTEGER DEFAULT 0,
            created_at TEXT,
            survey_date TEXT,
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
            bonus_adjustment REAL DEFAULT 0,
            current_balance REAL,
            problem_cost TEXT,
            notes TEXT,
            partnership_date TEXT,
            referral_count INTEGER,
            referral_payment TEXT,
            subscription_date TEXT,
            subscription_payment_date TEXT,
            purchases TEXT,
            sales TEXT,
            requisites TEXT,
            shop_id TEXT,
            business TEXT,
            products_services TEXT,
            account_status TEXT,
            requests_text TEXT,
            user_status TEXT,
            
            -- New fields for tracking origin/sync
            origin_bot TEXT,
            last_synced_at TEXT,
            
             -- Fields from schema reference that might be missing in some bots but present in db.py:
            updated_at TEXT,
            order_status TEXT,
            partner_auto_tech TEXT, 
            partner_auto_services TEXT,
            auto_purchases TEXT,
            auto_sales TEXT,
            operation_type TEXT,
            order_date TEXT,
            investment_program TEXT,
            investor_conditions TEXT,
            notified_at TEXT,
            proposal_status TEXT,
            last_proposal_notification TEXT,
            referrer_id INTEGER,
            purchases_count INTEGER DEFAULT 0,
            sales_count INTEGER DEFAULT 0,
            total_purchases REAL DEFAULT 0,
            total_sales REAL DEFAULT 0
        )
    """)
    
    # 2. USER_BONUSES Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_bonuses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bonus_total REAL,
            bonus_adjustment REAL DEFAULT 0,
            current_balance REAL,
            adjustment_reason TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    # 3. SURVEY_ANSWERS Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS survey_answers (
            answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question_id INTEGER,
            answer_text TEXT,
            answered_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    """)
    
    conn.commit()
    return conn

def get_table_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]

def migrate_bot(shared_conn, bot_path):
    bot_name = os.path.basename(bot_path)
    db_file = os.path.join(bot_path, "bot_database.db")
    
    if not os.path.exists(db_file):
        print(f"Skipping {bot_name}: No database found.")
        return

    print(f"Migrating from {bot_name}...")
    try:
        local_conn = sqlite3.connect(db_file)
        local_msg_cursor = local_conn.cursor()
        shared_cursor = shared_conn.cursor()
        
        # --- MIGRATE USERS ---
        try:
            local_msg_cursor.execute("SELECT * FROM users")
            columns = [description[0] for description in local_msg_cursor.description]
            rows = local_msg_cursor.fetchall()
            
            shared_user_columns = get_table_columns(shared_cursor, "users")
            
            for row in rows:
                user_data = dict(zip(columns, row))
                user_id = user_data.get("user_id")
                
                # Check if user exists in shared DB to prioritize data
                shared_cursor.execute("SELECT has_completed_survey, updated_at FROM users WHERE user_id = ?", (user_id,))
                existing = shared_cursor.fetchone()
                
                should_update = True
                if existing:
                    # Logic: if existing (shared) has survey completed, and local doesn't, keep shared.
                    # Or just prefer the one with more data. 
                    # Simple rule: If local has survey completed, update. Else, strictly if it's newer?
                    # Let's just merge non-empty fields.
                    pass
                
                # Construct query
                # Filter user_data to only include columns that exist in shared DB
                clean_user_data = {k: v for k, v in user_data.items() if k in shared_user_columns}
                clean_user_data['origin_bot'] = bot_name
                clean_user_data['last_synced_at'] = time.strftime('%Y-%m-%d %H:%M:%S')

                cols = ', '.join(clean_user_data.keys())
                placeholders = ', '.join(['?'] * len(clean_user_data))
                sql = f"INSERT OR REPLACE INTO users ({cols}) VALUES ({placeholders})"
                
                try:
                    shared_cursor.execute(sql, list(clean_user_data.values()))
                except Exception as e:
                    print(f"Error inserting user {user_id}: {e}")

            print(f"  - Migrated {len(rows)} users.")
            
        except sqlite3.OperationalError as e:
             print(f"  - Error reading users table: {e}")

        # --- MIGRATE BONUSES ---
        try:
            local_msg_cursor.execute("SELECT * FROM user_bonuses")
            columns = [description[0] for description in local_msg_cursor.description]
            rows = local_msg_cursor.fetchall()
            
            shared_bonus_columns = get_table_columns(shared_cursor, "user_bonuses")

            for row in rows:
                data = dict(zip(columns, row))
                
                # We need to treat ID carefully. AUTOINCREMENT in local vs shared.
                # BETTER: Insert without ID, let shared auto-increment.
                if 'id' in data:
                    del data['id']
                
                # Check if bonus record exists for this user to avoid duplication?
                # Actually user_bonuses is usually 1-to-1 with users in this schema.
                user_id = data.get('user_id')
                shared_cursor.execute("SELECT id FROM user_bonuses WHERE user_id=?", (user_id,))
                existing_bonus = shared_cursor.fetchone()
                
                if existing_bonus:
                    # Update existing
                    clean_data = {k: v for k, v in data.items() if k in shared_bonus_columns}
                    set_clause = ', '.join([f"{k}=?" for k in clean_data.keys()])
                    sql = f"UPDATE user_bonuses SET {set_clause} WHERE user_id=?"
                    shared_cursor.execute(sql, list(clean_data.values()) + [user_id])
                else:
                    # Insert new
                    clean_data = {k: v for k, v in data.items() if k in shared_bonus_columns}
                    cols = ', '.join(clean_data.keys())
                    placeholders = ', '.join(['?'] * len(clean_data))
                    sql = f"INSERT INTO user_bonuses ({cols}) VALUES ({placeholders})"
                    shared_cursor.execute(sql, list(clean_data.values()))

            print(f"  - Migrated {len(rows)} bonus records.")

        except sqlite3.OperationalError as e:
             print(f"  - Error reading user_bonuses table: {e}")

        # --- MIGRATE SURVEY ANSWERS ---
        try:
            local_msg_cursor.execute("SELECT * FROM survey_answers")
            columns = [description[0] for description in local_msg_cursor.description]
            rows = local_msg_cursor.fetchall()
            shared_columns = get_table_columns(shared_cursor, "survey_answers")

            count = 0
            for row in rows:
                data = dict(zip(columns, row))
                if 'answer_id' in data:
                    del data['answer_id'] # Let shared DB handle ID
                
                user_id = data.get('user_id')
                question_id = data.get('question_id')
                
                # Deduplicate based on user_id + question_id
                shared_cursor.execute("SELECT answer_id FROM survey_answers WHERE user_id=? AND question_id=?", (user_id, question_id))
                existing = shared_cursor.fetchone()
                
                if not existing:
                    clean_data = {k: v for k, v in data.items() if k in shared_columns}
                    cols = ', '.join(clean_data.keys())
                    placeholders = ', '.join(['?'] * len(clean_data))
                    sql = f"INSERT INTO survey_answers ({cols}) VALUES ({placeholders})"
                    shared_cursor.execute(sql, list(clean_data.values()))
                    count += 1
            
            print(f"  - Migrated {count} survey answers.")
            
        except sqlite3.OperationalError as e:
            print(f"  - Error reading survey_answers table: {e}")


        local_conn.close()
        shared_conn.commit()

    except Exception as e:
        print(f"Failed to migrate {bot_name}: {e}")

def main():
    if os.path.exists(SHARED_DB_PATH):
        print(f"Shared DB already exists at {SHARED_DB_PATH}. Removing to start fresh migration...")
        os.remove(SHARED_DB_PATH)
        
    shared_conn = init_shared_db()
    
    for bot_dir in BOT_DIRS:
        migrate_bot(shared_conn, bot_dir)
        
    shared_conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    main()
