# Medical Store Expiry & Inventory Alert System — MVP

Tracks pharmacy stock and flags what's expiring soon or running low. **No
external APIs, no AI needed, no cost at all** — this is pure logic (date math
and threshold checks), so it's simpler and lighter than the support-triage project.

## Solving the "I don't have real data" problem

This is the most common blocker when building something like this before
you have a customer. The approach:

1. **Build and test against realistic fake data first** — `sample_data.py`
   generates ~40 synthetic inventory items with common generic medicine
   names, random batches, and a realistic mix of expiry dates and stock
   levels (some expiring soon, some low stock, most totally normal — so
   your demo doesn't look artificially alarming).
2. **When you get a real pharmacy customer**, don't touch any code. Just
   use the **Upload CSV** option in the dashboard sidebar to load their
   actual inventory. Most pharmacies already track stock in Excel or a
   basic POS system, so exporting to CSV is usually a 2-minute task for them.
3. The CSV just needs these columns: `medicine_name`, `quantity`, `expiry_date`
   (optionally also `batch_number`, `supplier`, `unit_price`).

This means the exact same system you demo with fake data today is the real
product tomorrow — nothing to rebuild.

---

## Setup (a few minutes)

```bash
pip install -r requirements.txt
```

That's it — no API keys, no accounts, no external services.

## Running it

```bash
streamlit run app.py
```

Then in the sidebar, click **Load sample data (demo)** to try it out immediately
with realistic fake inventory. Explore the tabs:
- **Expiring soon** — items within 60 days of expiry
- **Already expired** — items that should be pulled from the shelf
- **Low stock** — items running low, with an inline quantity editor
- **Full inventory** — the complete table

## Customizing thresholds
Edit `config.py`:
```python
EXPIRY_WARNING_DAYS = 60   # change to whatever warning window makes sense
LOW_STOCK_THRESHOLD = 15   # change based on typical order volumes
```
Different pharmacies may want different thresholds (a busy pharmacy might
want a 90-day expiry warning; a small one might want 30).

## Project files

| File | Purpose |
|---|---|
| `config.py` | Alert thresholds |
| `database.py` | SQLite storage for inventory |
| `sample_data.py` | Generates realistic fake inventory for testing/demos |
| `alert_engine.py` | The actual logic — checks expiry dates and stock levels |
| `app.py` | The dashboard — run this |

## Ideas for pitching this to a real pharmacy
- Ask to see their current process first (usually a physical register or a messy Excel sheet) — that's your strongest pitch material
- Emphasize the **money saved from reduced wastage**, not the technology
- Offer to load their real data into a working demo during the sales conversation — much more convincing than talking about it abstractly

## Known limitations (be upfront about these)
- Single-user, single-location for now — no multi-branch support yet
- Runs on your machine — for a real customer, you'd eventually host this so it's accessible without your laptop being on
- No barcode scanning or POS integration yet — manual CSV upload only
