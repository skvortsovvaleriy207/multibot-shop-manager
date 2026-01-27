
# --- BOT SPECIFIC LOGIC ---

async def ensure_bot_data_exists(user_id, bot_name):
    """Ensure a row exists for this user and bot"""
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(SHARED_DB_FILE) as db:
        await db.execute("""
            INSERT OR IGNORE INTO bot_specific_data (user_id, bot_name, balance, account_status, user_status, updated_at)
            VALUES (?, ?, 0, 'Работа', 'Подписчик', ?)
        """, (user_id, bot_name, updated_at))
        await db.commit()

async def update_bot_balance(user_id, amount, bot_name):
    """Add amount to specific bot balance"""
    await ensure_bot_data_exists(user_id, bot_name)
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    async with aiosqlite.connect(SHARED_DB_FILE) as db:
        await db.execute("""
            UPDATE bot_specific_data 
            SET balance = balance + ?, updated_at = ?
            WHERE user_id = ? AND bot_name = ?
        """, (amount, updated_at, user_id, bot_name))
        await db.commit()

async def get_bot_balance(user_id, bot_name):
    """Get balance for specific bot"""
    await ensure_bot_data_exists(user_id, bot_name)
    async with aiosqlite.connect(SHARED_DB_FILE) as db:
        cursor = await db.execute("SELECT balance FROM bot_specific_data WHERE user_id = ? AND bot_name = ?", (user_id, bot_name))
        row = await cursor.fetchone()
        return row[0] if row else 0.0

async def get_bot_status(user_id, bot_name):
    """Get account_status for specific bot. Return 'Работа' if not found."""
    # Note: Don't auto-create here to avoid writing on simple checks, but safe to default
    async with aiosqlite.connect(SHARED_DB_FILE) as db:
        cursor = await db.execute("SELECT account_status FROM bot_specific_data WHERE user_id = ? AND bot_name = ?", (user_id, bot_name))
        row = await cursor.fetchone()
        return row[0] if row else 'Работа'
