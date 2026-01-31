import aiosqlite
import asyncio

async def inspect():
    try:
        async with aiosqlite.connect("bestsocialbot/bot_database.db") as db:
            cursor = await db.execute("SELECT user_id, has_completed_survey, account_status, username, first_name FROM users")
            rows = await cursor.fetchall()
            print(f"Total users found: {len(rows)}")
            for row in rows:
                print(f"User: {row[0]}, Survey: {row[1]}, Status: {row[2]}, Username: {row[3]}, Name: {row[4]}")
                
            cursor = await db.execute("SELECT * FROM survey_answers WHERE user_id = ?", (rows[0][0],)) if rows else None
            if cursor:
                answers = await cursor.fetchall()
                print(f"Survey Answers for {rows[0][0]}:Count={len(answers)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(inspect())
