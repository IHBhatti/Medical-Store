"""
sample_data.py
--------------
Since you don't have real pharmacy data yet, this generates a realistic
FAKE inventory so you can build, test, and demo the whole system before
your first real customer.

The medicine names below are common, publicly known generic drug names
(paracetamol, amoxicillin, etc.) — not pulled from any proprietary dataset.

When you get a real pharmacy as a customer: don't touch this file.
Instead use the "Upload CSV" option in the dashboard (app.py) to load
their actual inventory export — the rest of the system doesn't change.
"""

import random
from datetime import date, timedelta

from database import init_db, clear_inventory, insert_medicine

# Common generic medicine names, varied dosage forms — realistic mix for a
# general pharmacy (pain relief, antibiotics, chronic-illness meds, etc.)
MEDICINES = [
    "Paracetamol 500mg", "Ibuprofen 400mg", "Amoxicillin 250mg", "Azithromycin 500mg",
    "Omeprazole 20mg", "Metformin 500mg", "Amlodipine 5mg", "Atorvastatin 10mg",
    "Cetirizine 10mg", "Loratadine 10mg", "Aspirin 75mg", "Losartan 50mg",
    "Vitamin D3 60000 IU", "Vitamin C 500mg", "ORS Sachets", "Domperidone 10mg",
    "Ranitidine 150mg", "Ciprofloxacin 500mg", "Diclofenac Gel", "Salbutamol Inhaler",
    "Insulin Glargine", "Metronidazole 400mg", "Folic Acid 5mg", "Calcium Carbonate 500mg",
    "Multivitamin Syrup", "Cough Syrup (Dextromethorphan)", "ORS + Zinc Syrup",
    "Pantoprazole 40mg", "Levothyroxine 50mcg", "Clopidogrel 75mg",
]

SUPPLIERS = ["MediSupply Co.", "HealthLine Distributors", "PharmaCore Ltd.", "National Drug House"]


def generate_sample_inventory(num_items=40):
    """
    Builds a realistic fake inventory:
    - Some items expiring soon (to test the expiry alert)
    - Some items low in stock (to test the low-stock alert)
    - Most items perfectly normal (so alerts don't drown in noise)
    """
    init_db()
    clear_inventory()

    today = date.today()

    for i in range(num_items):
        medicine = random.choice(MEDICINES)
        batch_number = f"B{random.randint(1000, 9999)}"
        supplier = random.choice(SUPPLIERS)
        unit_price = round(random.uniform(2, 150), 2)

        # Weighted so the demo has a realistic mix: mostly fine, some
        # genuinely expiring soon, some genuinely low stock.
        situation = random.choices(
            ["normal", "expiring_soon", "low_stock", "both"],
            weights=[60, 15, 15, 10],
        )[0]

        if situation == "normal":
            expiry_date = today + timedelta(days=random.randint(90, 720))
            quantity = random.randint(20, 200)
        elif situation == "expiring_soon":
            expiry_date = today + timedelta(days=random.randint(1, 55))
            quantity = random.randint(20, 200)
        elif situation == "low_stock":
            expiry_date = today + timedelta(days=random.randint(90, 720))
            quantity = random.randint(0, 14)
        else:  # both
            expiry_date = today + timedelta(days=random.randint(1, 55))
            quantity = random.randint(0, 14)

        insert_medicine(
            medicine_name=medicine,
            batch_number=batch_number,
            quantity=quantity,
            expiry_date=expiry_date.isoformat(),
            supplier=supplier,
            unit_price=unit_price,
        )

    print(f"Generated {num_items} sample inventory items in {config_db_name()}.")


def config_db_name():
    from config import DB_FILE
    return DB_FILE


if __name__ == "__main__":
    generate_sample_inventory()
