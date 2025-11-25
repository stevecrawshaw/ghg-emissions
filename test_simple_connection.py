"""Simplified connection test without database specification."""

import os
from dotenv import load_dotenv
import duckdb

load_dotenv()

token = os.getenv("MOTHERDUCK_TOKEN")
print(f"Token loaded: {len(token)} chars")

# Try connecting without specifying database
print("\n1. Attempting connection to MotherDuck (no database)...")
try:
    conn = duckdb.connect(f"md:?motherduck_token={token}")
    print("[OK] Connected successfully!")

    # List available databases
    print("\n2. Listing databases...")
    result = conn.sql("SHOW DATABASES").fetchall()
    print("Available databases:")
    for row in result:
        print(f"  - {row[0]}")

    # Check if mca_data exists
    db_names = [row[0] for row in result]
    if 'mca_data' in db_names:
        print("\n[OK] mca_data database found!")

        # Try to use it
        print("\n3. Connecting to mca_data...")
        conn.sql("USE mca_data")
        tables = conn.sql("SHOW TABLES").fetchall()
        print(f"[OK] Found {len(tables)} tables in mca_data")
    else:
        print("\n[ERROR] mca_data database NOT FOUND in your MotherDuck account")
        print("Available databases:", db_names)

    conn.close()

except Exception as e:
    print(f"[ERROR] {e}")
