#!/usr/bin/env python3
"""
Migration runner for CosmoFolio database
Applies SQL migrations to Supabase PostgreSQL database
"""

import os
import sys
from pathlib import Path
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY environment variables not set")
    sys.exit(1)

def run_migrations():
    """Read and execute migrations.sql file"""

    # Initialize Supabase client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Read migrations file
    migrations_path = Path(__file__).parent / "migrations.sql"

    if not migrations_path.exists():
        print(f"ERROR: migrations.sql not found at {migrations_path}")
        sys.exit(1)

    with open(migrations_path, 'r') as f:
        migrations_sql = f.read()

    # Split by statement (semicolon-separated)
    statements = [s.strip() for s in migrations_sql.split(';') if s.strip()]

    print(f"Found {len(statements)} migration statements")
    print("=" * 60)

    # Execute each statement
    executed = 0
    skipped = 0

    for i, statement in enumerate(statements, 1):
        try:
            # Skip comments
            if statement.startswith('--'):
                skipped += 1
                continue

            print(f"[{i}/{len(statements)}] Executing migration...")

            # Execute using Supabase RPC or direct SQL
            # For complex migrations, we'll use postgres connection
            response = supabase.rpc("exec_sql", {"sql": statement}).execute()

            executed += 1
            print(f"✓ Completed")

        except Exception as e:
            print(f"✗ Failed: {str(e)}")
            # Continue to next statement rather than failing completely
            # Some statements might fail due to existing objects
            continue

    print("=" * 60)
    print(f"Migration complete!")
    print(f"  Executed: {executed}")
    print(f"  Skipped: {skipped}")
    print(f"  Total: {len(statements)}")

if __name__ == "__main__":
    print("CosmoFolio Database Migration")
    print("=" * 60)
    print(f"Supabase URL: {SUPABASE_URL}")
    print()

    response = input("Continue with migrations? (yes/no): ").lower()

    if response in ["yes", "y"]:
        run_migrations()
    else:
        print("Migration cancelled")
        sys.exit(0)
