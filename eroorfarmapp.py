# ================================
# INSTALL (run once in terminal or Colab)
# pip install streamlit pandas reportlab python-barcode pillow matplotlib
# ================================

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import barcode
from barcode.writer import ImageWriter
import os
import matplotlib.pyplot as plt

# ================================
# DATABASE
# ================================
conn = sqlite3.connect("mushroom.db", check_same_thread=False)
c = conn.cursor()

# Tables
c.execute('''CREATE TABLE IF NOT EXISTS sales(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT, client TEXT, mobile TEXT,
    product TEXT, qty REAL, rate REAL,
    total REAL, purchase_count INTEGER,
    reward TEXT, free_qty INTEGER
)''')

c.execute('''CREATE TABLE IF NOT EXISTS expenses(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT, category TEXT, amount REAL
)''')

c.execute('''CREATE TABLE IF NOT EXISTS production(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT, batch TEXT, bags INTEGER, yield REAL
)''')

c.execute('''CREATE TABLE IF NOT EXISTS inventory(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT, item TEXT, in_qty REAL, out_qty REAL
)''')

conn.commit()

# ================================
# HELPER FUNCTIONS
# ================================
def get_purchase_count(client):
    df = pd.read_sql_query("SELECT * FROM sales WHERE client=?", conn, params=(client,))
    return len(df) + 1

def generate_invoice(client, qty, rate, total):
    file_name = f"invoice_{client}_{datetime.now().timestamp()}.pdf"
    doc = SimpleDocTemplate(file_name)
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("MUSHROOM FARM INVOICE", styles['Title']))
    content.append(Spacer(1,10))
    content.append(Paragraph(f"Client: {client}", styles['Normal']))
    content.append(Paragraph(f"Qty: {qty} kg", styles['Normal']))
    content.append(Paragraph(f"Rate: ₹{rate}", styles['Normal']))
    content.append(Paragraph(f"Total: ₹{total}", styles['Normal']))
    content.append(Spacer(1,10))

    doc.build(content)
    return file_name

def generate_barcode(code_text):
    code = barcode.get('code128', code_text, writer=ImageWriter())
    filename = code.save("barcode")
    return filename

# ================================
# UI
# ================================
st.title("🍄 Mushroom Farm Mobile App")

menu = st.sidebar.selectbox("Menu", ["Dashboard","Sales Entry","Expenses","Production","Inventory"])

# ================================
# SALES ENTRY
# ================================
if menu == "Sales Entry":
    st.header("📱 Sales Entry")

    client = st.text_input("Client Name")
    mobile = st.text_input("Mobile")
    product = st.text_input("Product", "Oyster Mushroom")
    qty = st.number_input("Quantity (kg)", 0.0)
    rate = st.number_input("Rate ₹", 0.0)

    if st.button("Save Sale"):
        total = qty * rate
        count = get_purchase_count(client)
        reward = "YES" if count % 10 == 0 else ""
        free_qty = 1 if count % 10 == 0 else 0

        c.execute("INSERT INTO sales(date,client,mobile,product,qty,rate,total,purchase_count,reward,free_qty) VALUES(?,?,?,?,?,?,?,?,?,?)",
                  (datetime.now().strftime("%Y-%m-%d"), client, mobile, product, qty, rate, total, count, reward, free_qty))
        conn.commit()

        st.success(f"Saved! Total ₹{total}")

        # Generate invoice
        pdf = generate_invoice(client, qty, rate, total)
        st.download_button("Download Invoice", open(pdf, "rb"), file_name=pdf)

        # Barcode
        bc = generate_barcode(str(datetime.now().timestamp()))
        st.image(bc, caption="Barcode")

        # WhatsApp link
        if reward == "YES":
            msg = f"Dear {client}, you earned reward 🎉"
            wa = f"https://wa.me/{mobile}?text={msg}"
            st.markdown(f"[Send WhatsApp Message]({wa})")

# ================================
# DASHBOARD
# ================================
if menu == "Dashboard":
    st.header("📊 Dashboard")

    df = pd.read_sql_query("SELECT * FROM sales", conn)

    if not df.empty:
        total_sales = df["total"].sum()
        total_qty = df["qty"].sum()
        cost = total_qty * 120
        profit = total_sales - cost

        st.metric("Total Sales ₹", total_sales)
        st.metric("Profit ₹", profit)

        # Chart
        summary = df.groupby("client")["total"].sum()
        st.bar_chart(summary)

# ================================
# EXPENSES
# ================================
if menu == "Expenses":
    st.header("💸 Expenses")

    cat = st.text_input("Category")
    amt = st.number_input("Amount", 0.0)

    if st.button("Add Expense"):
        c.execute("INSERT INTO expenses(date,category,amount) VALUES(?,?,?)",
                  (datetime.now().strftime("%Y-%m-%d"), cat, amt))
        conn.commit()
        st.success("Expense Added")

# ================================
# PRODUCTION
# ================================
if menu == "Production":
    st.header("🍄 Production")

    batch = st.text_input("Batch")
    bags = st.number_input("Bags", 0)
    yield_bag = st.number_input("Yield per bag", 0.0)

    if st.button("Save Production"):
        c.execute("INSERT INTO production(date,batch,bags,yield) VALUES(?,?,?,?)",
                  (datetime.now().strftime("%Y-%m-%d"), batch, bags, yield_bag))
        conn.commit()
        st.success("Saved")

# ================================
# INVENTORY
# ================================
if menu == "Inventory":
    st.header("📦 Inventory")

    item = st.text_input("Item")
    inq = st.number_input("In Qty", 0.0)
    outq = st.number_input("Out Qty", 0.0)

    if st.button("Update Inventory"):
        c.execute("INSERT INTO inventory(date,item,in_qty,out_qty) VALUES(?,?,?,?)",
                  (datetime.now().strftime("%Y-%m-%d"), item, inq, outq))
        conn.commit()
        st.success("Updated")
