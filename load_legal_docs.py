import asyncio
import os
import sys

# Add project root to path to import shared_storage
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared_storage.global_db import save_legal_document, init_global_db

PRIVACY_POLICY_PATH = 'temp/Политика конфиденциальности данных.txt'
USER_AGREEMENT_PATH = 'temp/Пользовательское соглашение.txt'

async def main():
    print("Initializing global DB...")
    await init_global_db()

    # Load Privacy Policy
    if os.path.exists(PRIVACY_POLICY_PATH):
        print(f"Loading {PRIVACY_POLICY_PATH}...")
        with open(PRIVACY_POLICY_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Read {len(content)} chars from {PRIVACY_POLICY_PATH}")
            await save_legal_document('privacy_policy', content)
        print("✅ Privacy Policy loaded.")
    else:
        print(f"❌ File not found: {PRIVACY_POLICY_PATH}")

    # Load User Agreement
    if os.path.exists(USER_AGREEMENT_PATH):
        print(f"Loading {USER_AGREEMENT_PATH}...")
        with open(USER_AGREEMENT_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Read {len(content)} chars from {USER_AGREEMENT_PATH}")
            await save_legal_document('user_agreement', content)
        print("✅ User Agreement loaded.")
    else:
        print(f"❌ File not found: {USER_AGREEMENT_PATH}")

    # Verify
    from shared_storage.global_db import get_legal_document
    priv = await get_legal_document('privacy_policy')
    terms = await get_legal_document('user_agreement')
    print(f"Verification: Privacy={len(priv) if priv else 0}, Terms={len(terms) if terms else 0}")

if __name__ == "__main__":
    asyncio.run(main())
