import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = 'leads.db'

@st.cache_data
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            source TEXT,
            status TEXT DEFAULT 'New',
            score INTEGER DEFAULT 0,
            last_contact DATE,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_lead(name, email, phone, source, score, notes):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO leads (name, email, phone, source, status, score, last_contact, notes)
            VALUES (?, ?, ?, ?, 'New', ?, ?, ?)
        ''', (name, email, phone, source, score, datetime.now().strftime('%Y-%m-%d'), notes))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("Email already exists!")
        return False
    finally:
        conn.close()

def get_leads(status_filter=None):
    conn = sqlite3.connect(DB_FILE)
    query = "SELECT * FROM leads"
    if status_filter:
        query += f" WHERE status = '{status_filter}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def update_status(email, new_status):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE leads SET status = ? WHERE email = ?", (new_status, email))
    conn.commit()
    conn.close()

# Streamlit UI
st.set_page_config(page_title="Lead Manager", layout="wide")
st.title("🚀 Lead Management System")

init_db()

tab1, tab2, tab3 = st.tabs(["Add Lead", "View Leads", "Export"])

with tab1:
    st.header("Add New Lead")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
    with col2:
        source = st.selectbox("Source", ["Manual", "LinkedIn", "Website", "Instagram"])
        score = st.slider("Lead Score (0-100)", 0, 100, 50)
        notes = st.text_area("Notes")
    if st.button("Add Lead"):
        if add_lead(name, email, phone, source, score, notes):
            st.success("Lead added!")

with tab2:
    st.header("Leads Dashboard")
    status_filter = st.selectbox("Filter by Status", ["All", "New", "Contacted", "Qualified", "Closed"])
    df = get_leads(status_filter if status_filter != "All" else None)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        # Update status
        selected_email = st.selectbox("Select Email to Update", df['email'].tolist() if not df.empty else [])
        new_status = st.selectbox("New Status", ["New", "Contacted", "Qualified", "Closed"])
        if st.button("Update Status") and selected_email:
            update_status(selected_email, new_status)
            st.rerun()
    else:
        st.info("No leads yet.")

with tab3:
    st.header("Export & Reports")
    df_all = get_leads()
    if st.button("Export to CSV"):
        csv = df_all.to_csv(index=False).encode('utf-8')
        st.download_button("Download leads.csv", csv, "leads.csv", "text/csv")
    st.metric("Total Leads", len(df_all))
    st.metric("New Leads", len(get_leads("New")))
