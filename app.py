"""
app.py
------
Run with:  streamlit run app.py

Shows the current inventory, flags expiring/low-stock items, lets the owner
search for any medicine instantly, and supports quick day-to-day restocking.
"""

import pandas as pd
import streamlit as st
from datetime import date

from config import EXPIRY_WARNING_DAYS, LOW_STOCK_THRESHOLD
from database import (
    init_db, get_all_inventory, clear_inventory, insert_medicine,
    update_quantity, add_quantity, delete_item,
)
from alert_engine import check_alerts
from sample_data import generate_sample_inventory

st.set_page_config(page_title="Pharmacy Inventory Alerts", page_icon="💊", layout="wide")
init_db()

# --- Visual styling: colored status pills, consistent with a traffic-light convention ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.status-pill {
    display: inline-block;
    font-size: 12px;
    font-weight: 500;
    padding: 4px 10px;
    border-radius: 6px;
}
.pill-expired  { background: #FCEBEB; color: #791F1F; }
.pill-warning  { background: #FAEEDA; color: #854F0B; }
.pill-lowstock { background: #E6F1FB; color: #0C447C; }
.pill-ok       { background: #EAF3DE; color: #27500A; }

.item-name { font-size: 15px; font-weight: 500; margin: 0; }
.item-meta { font-size: 12px; color: #888780; margin: 0; font-family: 'JetBrains Mono', monospace; }
</style>
""", unsafe_allow_html=True)

st.markdown("### 💊 Medical Store Inventory & Expiry Alerts")
st.caption("Tracks stock levels and expiry dates, and flags what needs attention.")

# --- Sidebar: data controls ---
with st.sidebar:
    st.subheader("Data")

    if st.button("Load sample data (demo)", use_container_width=True):
        generate_sample_inventory()
        st.success("Sample inventory loaded.")
        st.rerun()

    st.divider()
    st.caption(
        "Day-to-day restocking: use the **Add new stock** tab — no need to "
        "touch a CSV each time. Use CSV upload below only for a bulk import "
        "(e.g. the very first time you set this up)."
    )

    csv_mode = st.radio(
        "CSV upload mode",
        ["Append to existing inventory", "Replace everything"],
        help="Append adds these rows on top of what's already there. Replace wipes the current inventory first.",
    )

    uploaded_file = st.file_uploader(
        "Upload CSV (columns: medicine_name, batch_number, quantity, expiry_date)",
        type=["csv"],
    )
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        required_cols = {"medicine_name", "quantity", "expiry_date"}
        if not required_cols.issubset(set(df.columns)):
            st.error(f"CSV must include at least these columns: {', '.join(required_cols)}")
        else:
            if csv_mode == "Replace everything":
                clear_inventory()
            for _, row in df.iterrows():
                insert_medicine(
                    medicine_name=row["medicine_name"],
                    batch_number=row.get("batch_number", ""),
                    quantity=int(row["quantity"]),
                    expiry_date=pd.to_datetime(row["expiry_date"]).date().isoformat(),
                    supplier=row.get("supplier", ""),
                    unit_price=float(row.get("unit_price", 0.0)),
                )
            st.success(f"Loaded {len(df)} items from your CSV.")
            st.rerun()

# --- Load inventory + run alert checks ---
inventory = get_all_inventory()

if not inventory:
    st.info("No inventory yet. Add your first item in the **Add new stock** tab below, load sample data, or upload a CSV from the sidebar.")

alerts = check_alerts(inventory) if inventory else {"expiring_soon": [], "already_expired": [], "low_stock": []}
expired_ids = {item["id"] for item in alerts["already_expired"]}
expiring_ids = {item["id"] for item in alerts["expiring_soon"]}
low_stock_ids = {item["id"] for item in alerts["low_stock"]}


def status_pill_html(item):
    """Build the little colored status pill for one inventory item, based on its worst issue."""
    if item["id"] in expired_ids:
        days = abs([i for i in alerts["already_expired"] if i["id"] == item["id"]][0]["days_left"])
        return f'<span class="status-pill pill-expired">Expired {days}d ago</span>'
    if item["id"] in expiring_ids:
        days = [i for i in alerts["expiring_soon"] if i["id"] == item["id"]][0]["days_left"]
        return f'<span class="status-pill pill-warning">{days}d left</span>'
    if item["id"] in low_stock_ids:
        return f'<span class="status-pill pill-lowstock">{item["quantity"]} units left</span>'
    return '<span class="status-pill pill-ok">In stock</span>'


# --- Metric row (color-coded to match the pills above) ---
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total items", len(inventory))
m2.metric("Expiring soon", len(alerts["expiring_soon"]))
m3.metric("Already expired", len(alerts["already_expired"]))
m4.metric("Low stock", len(alerts["low_stock"]))

st.divider()

# --- Search bar ---
search_query = st.text_input(
    "Search medicines",
    placeholder="Search by medicine name, batch number, or supplier...",
    label_visibility="collapsed",
)

if search_query:
    query_lower = search_query.strip().lower()
    matches = [
        item for item in inventory
        if query_lower in item["medicine_name"].lower()
        or query_lower in (item["batch_number"] or "").lower()
        or query_lower in (item["supplier"] or "").lower()
    ]

    st.caption(f"{len(matches)} result(s) for \"{search_query}\"")

    if not matches:
        st.info("No matching medicines. Try a different name or check the spelling.")

    for item in matches:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.markdown(
                f'<p class="item-name">{item["medicine_name"]}</p>'
                f'<p class="item-meta">Batch {item["batch_number"]} &middot; {item["supplier"]}</p>',
                unsafe_allow_html=True,
            )
            c2.markdown(f"Qty: **{item['quantity']}**  \nExpires: {item['expiry_date']}")
            c3.markdown(status_pill_html(item), unsafe_allow_html=True)

    st.divider()

# --- Tabs for the rest of the workflow ---
tab0, tab1, tab2, tab3, tab4 = st.tabs(
    ["Add new stock", "Expiring soon", "Already expired", "Low stock", "Full inventory"]
)

with tab0:
    st.caption("Use this whenever new stock arrives — takes a few seconds, no CSV needed.")

    restock_col, new_col = st.columns(2)

    with restock_col:
        st.markdown("**Restock an existing medicine**")
        existing_names = sorted({item["medicine_name"] for item in inventory})
        if existing_names:
            with st.form("restock_form"):
                selected_name = st.selectbox("Medicine", existing_names)
                matching_batches = [
                    item for item in inventory if item["medicine_name"] == selected_name
                ]
                batch_labels = [f"Batch {item['batch_number']} (qty {item['quantity']})" for item in matching_batches]
                selected_batch_idx = st.selectbox(
                    "Batch", range(len(batch_labels)), format_func=lambda i: batch_labels[i]
                )
                add_amount = st.number_input("Quantity received", min_value=1, value=10)
                if st.form_submit_button("Add to stock", use_container_width=True):
                    item_id = matching_batches[selected_batch_idx]["id"]
                    add_quantity(item_id, add_amount)
                    st.success(f"Added {add_amount} units to {selected_name}.")
                    st.rerun()
        else:
            st.caption("No existing medicines yet — add one on the right first.")

    with new_col:
        st.markdown("**Add a brand new medicine or batch**")
        with st.form("new_medicine_form", clear_on_submit=True):
            medicine_name = st.text_input("Medicine name")
            batch_number = st.text_input("Batch number")
            quantity = st.number_input("Quantity", min_value=0, value=50)
            expiry_date_input = st.date_input("Expiry date")
            supplier = st.text_input("Supplier (optional)")
            unit_price = st.number_input("Unit price (optional)", min_value=0.0, value=0.0)
            if st.form_submit_button("Add new item", use_container_width=True):
                if not medicine_name.strip():
                    st.error("Medicine name is required.")
                else:
                    insert_medicine(
                        medicine_name=medicine_name.strip(),
                        batch_number=batch_number.strip(),
                        quantity=quantity,
                        expiry_date=expiry_date_input.isoformat(),
                        supplier=supplier.strip(),
                        unit_price=unit_price,
                    )
                    st.success(f"Added {medicine_name}.")
                    st.rerun()

with tab1:
    st.caption(f"Items expiring within {EXPIRY_WARNING_DAYS} days")
    if not alerts["expiring_soon"]:
        st.success("Nothing expiring soon.")
    for item in alerts["expiring_soon"]:
        with st.container(border=True):
            c1, c2 = st.columns([3, 2])
            c1.markdown(
                f'<p class="item-name">{item["medicine_name"]}</p>'
                f'<p class="item-meta">Batch {item["batch_number"]}</p>',
                unsafe_allow_html=True,
            )
            c2.markdown(status_pill_html(item), unsafe_allow_html=True)

with tab2:
    st.caption("Items past their expiry date — remove from shelf")
    if not alerts["already_expired"]:
        st.success("No expired items.")
    for item in alerts["already_expired"]:
        with st.container(border=True):
            c1, c2 = st.columns([3, 2])
            c1.markdown(
                f'<p class="item-name">{item["medicine_name"]}</p>'
                f'<p class="item-meta">Batch {item["batch_number"]}</p>',
                unsafe_allow_html=True,
            )
            c2.markdown(status_pill_html(item), unsafe_allow_html=True)

with tab3:
    st.caption(f"Items at or below {LOW_STOCK_THRESHOLD} units")
    if not alerts["low_stock"]:
        st.success("Nothing low on stock.")
    for item in alerts["low_stock"]:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.markdown(
                f'<p class="item-name">{item["medicine_name"]}</p>'
                f'<p class="item-meta">{item["supplier"]}</p>',
                unsafe_allow_html=True,
            )
            c2.markdown(status_pill_html(item), unsafe_allow_html=True)
            new_qty = c3.number_input("Update qty", min_value=0, value=item["quantity"], key=f"qty_{item['id']}", label_visibility="collapsed")
            if new_qty != item["quantity"]:
                update_quantity(item["id"], new_qty)
                st.rerun()

with tab4:
    df_display = pd.DataFrame(inventory)[["medicine_name", "batch_number", "quantity", "expiry_date", "supplier", "unit_price"]]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

st.divider()
st.caption("Tip: use the search bar above to quickly check any medicine's stock and expiry status.")
