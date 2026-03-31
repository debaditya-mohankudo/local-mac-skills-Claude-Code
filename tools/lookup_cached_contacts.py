#!/usr/bin/env python3
"""
lookup_cached_contacts.py — Search contacts by name or nickname from SQLite cache

Usage:
  python3 lookup_cached_contacts.py "search_term"
  lookup_cached_contacts.py "John Doe"
"""

import sqlite3
import sys
import os
from pathlib import Path
from tabulate import tabulate

def lookup_contacts(search_term: str) -> None:
    """Search contacts by name or nickname."""

    db_path = Path.home() / "Documents" / "claude_cache_data" / "personal_contacts.sqlite"

    # Validate database exists
    if not db_path.exists():
        print(f"❌ Error: Database not found at {db_path}")
        sys.exit(1)

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Query: search in both name and nicknames (case-insensitive)
        cursor.execute('''
            SELECT
                id,
                name,
                phone,
                COALESCE(nicknames, '—') as nicknames,
                lookup_count,
                COALESCE(substr(last_contacted, 1, 10), '—') as last_contacted
            FROM contacts
            WHERE (LOWER(name) LIKE LOWER(?) OR LOWER(nicknames) LIKE LOWER(?))
              AND archived = 0
            ORDER BY lookup_count DESC
        ''', (f'%{search_term}%', f'%{search_term}%'))

        results = cursor.fetchall()
        conn.close()

        # Check if any results found
        if not results:
            print(f"❌ No contacts found matching \"{search_term}\"")
            sys.exit(1)

        # Format and display results
        headers = ["ID", "Name", "Phone", "Nicknames", "Lookups", "Last Contact"]
        print(f"\n🔍 Contacts matching \"{search_term}\":\n")
        print(tabulate(results, headers=headers, tablefmt="grid"))
        print(f"\n✅ Found {len(results)} contact(s)\n")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: lookup_cached_contacts.py \"search_term\"")
        print("       lookup_cached_contacts.py \"John Doe\"")
        sys.exit(1)

    search_term = sys.argv[1]
    lookup_contacts(search_term)
