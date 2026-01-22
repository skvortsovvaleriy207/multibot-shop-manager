try:
    from google_sheets import sync_from_sheets_to_db
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
except SyntaxError as e:
    print(f"Syntax error: {e}")
except Exception as e:
    print(f"Other error: {e}")
