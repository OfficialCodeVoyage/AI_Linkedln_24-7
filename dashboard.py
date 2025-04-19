import os
import sqlite3
import time
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load environment
load_dotenv()
# Extract SQLite path from DB_URL env var
db_path = os.getenv("DB_URL", "sqlite:///state.db").split("sqlite:///")[-1]

# --- Database Connection & Setup ---
def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # Return rows as dict-like objects
    return conn

def ensure_db_table():
    conn = get_db_connection()
    conn.execute("CREATE TABLE IF NOT EXISTS actions(id INTEGER PRIMARY KEY, date TEXT, type TEXT, success INTEGER)")
    conn.commit()
    conn.close()

ensure_db_table() # Run once at startup

# --- Page Config ---
st.set_page_config(page_title="LinkedIn MCP Bot Dashboard", layout="wide")
st.title("📊 LinkedIn MCP Bot Dashboard")

# --- Auto-Refresh Control ---
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

refresh_toggle = st.checkbox("Auto-refresh every 60 seconds", value=st.session_state.auto_refresh)
st.session_state.auto_refresh = refresh_toggle

# --- Data Loading Functions ---
@st.cache_data(ttl=55) # Cache data for slightly less than refresh interval
def load_stats_data():
    conn = get_db_connection()
    stats_df = pd.read_sql(
        "SELECT date, type, COUNT(*) as count, SUM(success) as successes FROM actions GROUP BY date, type", conn
    )
    conn.close()
    return stats_df

@st.cache_data(ttl=55)
def load_recent_actions():
    conn = get_db_connection()
    recent_df = pd.read_sql(
        "SELECT id, date, type, success FROM actions ORDER BY id DESC LIMIT 250", conn
    )
    conn.close()
    return recent_df

# --- Load Data ---
stats_df = load_stats_data()
recent_df = load_recent_actions()

# --- Today's Summary Stats ---
st.subheader("Today's Activity Summary")
today_str = pd.Timestamp.now().strftime('%Y-%m-%d')
today_data = stats_df[stats_df['date'] == today_str]

total_actions_today = today_data['count'].sum()
successful_actions_today = today_data['successes'].sum()
success_rate_today = (successful_actions_today / total_actions_today * 100) if total_actions_today > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Actions Today", total_actions_today)
col2.metric("Successful Actions", successful_actions_today)
col3.metric("Success Rate", f"{success_rate_today:.1f}%")

# --- Daily Actions Chart ---
st.subheader("Daily Actions Over Time")
if not stats_df.empty:
    # Pivot for charting counts
    pivot_counts_df = stats_df.pivot(index="date", columns="type", values="count").fillna(0)
    st.line_chart(pivot_counts_df)
else:
    st.info("No action history to display yet.")

# --- Recent Actions Table ---
st.subheader("Recent Actions Log (Last 250)")
if not recent_df.empty:
    recent_df["status"] = recent_df["success"].apply(lambda x: "✔ Success" if x == 1 else "✖ Failure")
    st.dataframe(recent_df[["date", "type", "status"]], use_container_width=True)
    
    # Add clearer download button
    csv = recent_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 Download Recent Actions as CSV",
        data=csv,
        file_name="linkedin_bot_recent_actions.csv",
        mime='text/csv',
    )
else:
    st.info("No recent actions recorded yet.")

# --- Auto-Refresh Logic ---
if st.session_state.auto_refresh:
    time.sleep(60)
    st.rerun() 