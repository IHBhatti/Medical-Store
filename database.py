"""
database.py
-----------
Stores medicine inventory using SQLite — built into Python, no server needed.
"""

import sqlite3
from config import DB_FILE


def get_connection():
    return sqlite3.connect(DB_FILE)


def init_db():
    """Create the inventory table if it doesn't exist yet. Safe to call every run."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_name TEXT NOT NULL,
            batch_number TEXT,
            quantity INTEGER NOT NULL,
            expiry_date TEXT NOT NULL,   -- stored as YYYY-MM-DD
            supplier TEXT,
            unit_price REAL
        )
    """)
    conn.commit()
    conn.close()


def clear_inventory():
    """Wipe all rows — used when loading a fresh sample dataset or a new CSV."""
    conn = get_connection()
    conn.execute("DELETE FROM inventory")
    conn.commit()
    conn.close()


def insert_medicine(medicine_name, batch_number, quantity, expiry_date, supplier="", unit_price=0.0):
    conn = get_connection()
    conn.execute("""
        INSERT INTO inventory (medicine_name, batch_number, quantity, expiry_date, supplier, unit_price)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (medicine_name, batch_number, quantity, expiry_date, supplier, unit_price))
    conn.commit()
    conn.close()


def get_all_inventory():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory ORDER BY expiry_date ASC")
    columns = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    conn.close()
    return [dict(zip(columns, row)) for row in rows]


def update_quantity(item_id, new_quantity):
    conn = get_connection()
    conn.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (new_quantity, item_id))
    conn.commit()
    conn.close()


def add_quantity(item_id, amount):
    """Increase an existing item's quantity by `amount` — used when new stock of an existing batch arrives."""
    conn = get_connection()
    conn.execute("UPDATE inventory SET quantity = quantity + ? WHERE id = ?", (amount, item_id))
    conn.commit()
    conn.close()


def delete_item(item_id):
    conn = get_connection()
    conn.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
