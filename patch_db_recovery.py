import re

FILE_PATH = "investmentsbot/db.py"

def patch_db_init():
    with open(FILE_PATH, 'r') as f:
        content = f.read()

    # We want to inject shared db initialization.
    # We can detect "async def init_db():"
    
    # We will remove the "CREATE TABLE IF NOT EXISTS users" block from the main flow
    # And instead put it into a "async with aiosqlite.connect(SHARED_DB_FILE) as shared_db:" block.
    
    # Actually, keeping 'users' in Local DB doesn't hurt (it's just unused). 
    # But ensuring it exists in Shared DB is CRITICAL.
    
    # So I will simply ADD the shared initialization at the beginning of init_db.
    
    insertion_marker = "async def init_db():"
    
    shared_init_code = """
    # Initialize Shared DB Tables
    try:
        async with aiosqlite.connect(SHARED_DB_FILE) as shared_db:
            await shared_db.execute("PRAGMA journal_mode=WAL")
            await shared_db.execute(\"\"\"
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
                    bot_subscriptions TEXT,
                    updated_at TEXT,
                    order_status TEXT,
                    partner_auto_tech TEXT, 
                    partner_auto_services TEXT,
                    auto_purchases TEXT,
                    auto_sales TEXT,
                    operation_type TEXT DEFAULT 'sale_tech',
                    order_date TEXT,
                    purchases_count INTEGER DEFAULT 0,
                    sales_count INTEGER DEFAULT 0,
                    total_purchases REAL DEFAULT 0,
                    total_sales REAL DEFAULT 0,
                    investment_program TEXT,
                    investor_conditions TEXT,
                    notified_at TEXT,
                    proposal_status TEXT DEFAULT 'Новое предложение',
                    last_proposal_notification TEXT,
                    referrer_id INTEGER
                )
            \"\"\")
            
            await shared_db.execute(\"\"\"
                CREATE TABLE IF NOT EXISTS survey_answers (
                    answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    question_id INTEGER,
                    answer_text TEXT,
                    answered_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            \"\"\")
            
            await shared_db.execute(\"\"\"
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
            \"\"\")
            
            await shared_db.execute(\"\"\"
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER,
                    recipient_id INTEGER NOT NULL,
                    subject TEXT,
                    message_text TEXT NOT NULL,
                    sent_at TEXT,
                    is_read BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (sender_id) REFERENCES users (user_id),
                    FOREIGN KEY (recipient_id) REFERENCES users (user_id)
                )
            \"\"\")
            
             # Таблица партнеров по автотехнике согласно ТЗ п.3
            await shared_db.execute(\"\"\"
                CREATE TABLE IF NOT EXISTS auto_tech_partners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_name TEXT NOT NULL,
                    contact_info TEXT,
                    specialization TEXT,
                    status TEXT DEFAULT 'ПАРТНЕР',
                    created_at TEXT
                )
            \"\"\")
            
            # Таблица партнеров по автоуслугам согласно ТЗ п.4
            await shared_db.execute(\"\"\"
                CREATE TABLE IF NOT EXISTS auto_service_partners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    partner_name TEXT NOT NULL,
                    contact_info TEXT,
                    services TEXT,
                    status TEXT DEFAULT 'ПАРТНЕР',
                    created_at TEXT
                )
            \"\"\")
            
            # Таблица инвесторов согласно ТЗ п.5
            await shared_db.execute(\"\"\"
                CREATE TABLE IF NOT EXISTS investors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    investor_name TEXT NOT NULL,
                    contact_info TEXT,
                    investment_amount REAL,
                    status TEXT DEFAULT 'ИНВЕСТОР',
                    created_at TEXT
                )
            \"\"\")

            await shared_db.commit()
            print("Shared DB initialized successfully")
    except Exception as e:
        print(f"Error initializing Shared DB: {e}")
    """
    
    # Indent it correctly (4 spaces)
    # But wait, init_db is async def.
    # I should insert it INSIDE the function.
    
    lines = content.splitlines()
    new_lines = []
    
    for line in lines:
        new_lines.append(line)
        if line.strip().startswith("async def init_db():"):
            new_lines.append(shared_init_code)

    with open(FILE_PATH, 'w') as f:
        f.write("\n".join(new_lines))
    print("Patched investmentsbot/db.py")

if __name__ == "__main__":
    patch_db_init()
