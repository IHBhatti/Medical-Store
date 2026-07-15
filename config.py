"""
config.py
---------
All settings in one place.
"""

DB_FILE = "inventory.db"

# A medicine is flagged "expiring soon" if it expires within this many days
EXPIRY_WARNING_DAYS = 60

# A medicine is flagged "low stock" if quantity falls at or below this number
LOW_STOCK_THRESHOLD = 15
