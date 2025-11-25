"""Quick diagnostic script to test MotherDuck connection."""

import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if token is loaded
token = os.getenv("MOTHERDUCK_TOKEN")
print("=" * 60)
print("MotherDuck Connection Diagnostic")
print("=" * 60)

if not token:
    print("[ERROR] MOTHERDUCK_TOKEN not found in environment")
    print("\nChecklist:")
    print("  1. Verify .env file exists in project root")
    print("  2. Ensure it contains: MOTHERDUCK_TOKEN=your_token")
    print("  3. No spaces around the = sign")
    print("  4. Token is not wrapped in quotes")
    sys.exit(1)

print(f"[OK] MOTHERDUCK_TOKEN loaded (length: {len(token)} chars)")
print(f"     First 10 chars: {token[:10]}...")

# Test connection
print("\n" + "=" * 60)
print("Testing connection to MotherDuck...")
print("=" * 60)

try:
    from src.data.connections import get_connection, test_connection

    print("[...] Attempting connection...")
    conn = get_connection()
    print("[OK] Connection established!")

    print("[...] Running test query...")
    if test_connection(conn):
        print("[OK] Test query successful!")

        # Get table count
        tables = conn.sql(
            """
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = 'main'
            """
        ).fetchone()
        print(f"[OK] Found {tables[0]} tables in mca_data database")

        conn.close()
        print("\n" + "=" * 60)
        print("[SUCCESS] All checks passed! MotherDuck connection working.")
        print("=" * 60)
    else:
        print("[ERROR] Test query failed")
        sys.exit(1)

except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
    print("\nPossible issues:")
    print("  1. Invalid or expired token")
    print("  2. Network connectivity problems")
    print("  3. MotherDuck service unavailable")
    print("\nTo get a new token:")
    print("  -> Visit https://motherduck.com/")
    print("  -> Go to Settings > Personal Access Tokens")
    sys.exit(1)
