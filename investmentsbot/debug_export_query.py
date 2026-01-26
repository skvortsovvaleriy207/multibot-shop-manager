import sqlite3
import os

DB_FILE = "../shared_storage/bot_database.db"

def test_query():
    print(f"Testing exact export query from sync_db_to_main_survey_sheet")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        query = """
                SELECT DISTINCT
                    sa3.answer_text,
                    sa4.answer_text,
                    sa6.answer_text,
                    sa7.answer_text,
                    sa9.answer_text,
                    sa10.answer_text,
                    sa11.answer_text,
                    sa12.answer_text,
                    sa13.answer_text,
                    sa14.answer_text,
                    sa15.answer_text,
                    sa16.answer_text,
                    ub.bonus_total,
                    ub.bonus_adjustment,
                    ub.current_balance,
                    u.problem_cost,
                    u.notes,
                    u.partnership_date,
                    CAST(u.user_id AS TEXT),
                    u.referral_count,
                    u.referral_payment,
                    u.subscription_date,
                    u.subscription_payment_date,
                    u.purchases,
                    u.sales,
                    u.requisites,
                    u.shop_id,
                    u.business,
                    u.products_services,
                    u.account_status
                FROM users u
                LEFT JOIN user_bonuses ub ON u.user_id = ub.user_id
                LEFT JOIN survey_answers sa1 ON u.user_id = sa1.user_id AND sa1.question_id = 1
                LEFT JOIN survey_answers sa3 ON u.user_id = sa3.user_id AND sa3.question_id = 3
                LEFT JOIN survey_answers sa4 ON u.user_id = sa4.user_id AND sa4.question_id = 4
                LEFT JOIN survey_answers sa6 ON u.user_id = sa6.user_id AND sa6.question_id = 6
                LEFT JOIN survey_answers sa7 ON u.user_id = sa7.user_id AND sa7.question_id = 7
                LEFT JOIN survey_answers sa9 ON u.user_id = sa9.user_id AND sa9.question_id = 9
                LEFT JOIN survey_answers sa10 ON u.user_id = sa10.user_id AND sa10.question_id = 10
                LEFT JOIN survey_answers sa11 ON u.user_id = sa11.user_id AND sa11.question_id = 11
                LEFT JOIN survey_answers sa12 ON u.user_id = sa12.user_id AND sa12.question_id = 12
                LEFT JOIN survey_answers sa13 ON u.user_id = sa13.user_id AND sa13.question_id = 13
                LEFT JOIN survey_answers sa14 ON u.user_id = sa14.user_id AND sa14.question_id = 14
                LEFT JOIN survey_answers sa15 ON u.user_id = sa15.user_id AND sa15.question_id = 15
                LEFT JOIN survey_answers sa16 ON u.user_id = sa16.user_id AND sa16.question_id = 16
                WHERE u.user_id != 0
                GROUP BY u.user_id
                ORDER BY MAX(ub.updated_at) DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"Query returned {len(rows)} rows")
        if not rows:
            print("No rows returned!")
        for row in rows:
            # Print row but truncate long items for readability
            print(f"Row: {row}")
            
    except Exception as e:
        print(f"SQL Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_query()
