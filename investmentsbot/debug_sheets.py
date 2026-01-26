import asyncio
import gspread
from config import CREDENTIALS_FILE, MAIN_SURVEY_SHEET_URL
import os

def debug_sheet():
    print(f"Checking Sheet URL: {MAIN_SURVEY_SHEET_URL}")
    try:
        client = gspread.service_account(filename=CREDENTIALS_FILE)
        spreadsheet = client.open_by_url(MAIN_SURVEY_SHEET_URL)
        sheet = spreadsheet.worksheet("Основная таблица")
        all_values = sheet.get_all_values()
        print(f"Total rows found: {len(all_values)}")
        if len(all_values) > 0:
            print("Row 1 (Header):", all_values[0])
        if len(all_values) > 1:
            print("Row 2 (Data?):", all_values[1])
            
        # Check Partners sheet too
        try:
            sheet_p = spreadsheet.worksheet("Партнеры")
            print(f"Partners Sheet rows: {len(sheet_p.get_all_values())}")
        except:
            print("No Partners sheet")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    with open("debug_output.txt", "w") as f:
        import sys
        sys.stdout = f
        debug_sheet()
