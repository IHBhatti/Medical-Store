"""
alert_engine.py
---------------
Pure logic, no AI needed here — just date math and threshold checks.
This is what actually finds the problems the pharmacy owner cares about.
"""

from datetime import date, datetime

from config import EXPIRY_WARNING_DAYS, LOW_STOCK_THRESHOLD


def days_until_expiry(expiry_date_str):
    expiry = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
    return (expiry - date.today()).days


def check_alerts(inventory):
    """
    Takes the full inventory list and splits it into:
      - expiring_soon: items within EXPIRY_WARNING_DAYS of expiry (not yet expired)
      - already_expired: items past their expiry date entirely
      - low_stock: items at or below LOW_STOCK_THRESHOLD
    Returns a dict with all three lists, each item annotated with days_left.
    """
    expiring_soon = []
    already_expired = []
    low_stock = []

    for item in inventory:
        days_left = days_until_expiry(item["expiry_date"])
        item = {**item, "days_left": days_left}

        if days_left < 0:
            already_expired.append(item)
        elif days_left <= EXPIRY_WARNING_DAYS:
            expiring_soon.append(item)

        if item["quantity"] <= LOW_STOCK_THRESHOLD:
            low_stock.append(item)

    # Most urgent first
    expiring_soon.sort(key=lambda x: x["days_left"])
    already_expired.sort(key=lambda x: x["days_left"])
    low_stock.sort(key=lambda x: x["quantity"])

    return {
        "expiring_soon": expiring_soon,
        "already_expired": already_expired,
        "low_stock": low_stock,
    }
