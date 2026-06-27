import streamlit as st
import pandas as pd
import requests
import datetime

st.set_page_config(page_title="Buyback Announcements", page_icon="📋", layout="wide")

st.title("📋 Buyback Announcements")
st.caption("Latest buyback announcements from NSE — Nifty 500 companies highlighted")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer": "https://www.nseindia.com/",
    "Accept": "application/json",
}

@st.cache_data(ttl=3600)
def fetch_buybacks():
    session = requests.Session()
    # First hit NSE homepage to get cookies
    session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
    response = session.get(
        "https://www.nseindia.com/api/corporate-announcements?index=equities&subject=Buyback",
        headers=HEADERS,
        timeout=15
    )
    if response.status_code == 200:
        return response.json()
    return []

@st.cache_data
def load_nifty500():
    try:
        df = pd.read_csv("nifty500.csv")
        return set(df["Symbol"].astype(str).str.strip().tolist())
    except:
        return set()

nifty500_symbols = load_nifty500()

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

with st.spinner("Fetching latest buyback announcements..."):
    data = fetch_buybacks()

if not data:
    st.warning("Could not fetch data from NSE. Try refreshing!")
else:
    df = pd.DataFrame(data)
    
    # Filter Nifty 500 only toggle
    nifty_only = st.toggle("Show Nifty 500 companies only", value=True)
    
    if nifty_only and "symbol" in df.columns:
        df = df[df["symbol"].isin(nifty500_symbols)]

    st.success(f"Found {len(df)} buyback announcements!")
    
    # Highlight Nifty 500 companies
    if "symbol" in df.columns:
        df["Nifty 500"] = df["symbol"].apply(
            lambda x: "✅ Yes" if x in nifty500_symbols else "❌ No"
        )

    # Keep only useful columns
    useful_cols = [c for c in [
        "symbol", "companyName", "subject", 
        "bm_desc", "attchmntText", "sort_date"
    ] if c in df.columns]
    
    df = df[useful_cols].rename(columns={
        "symbol": "Symbol",
        "companyName": "Company",
        "subject": "Subject",
        "bm_desc": "Details",
        "attchmntText": "Announcement",
        "sort_date": "Date"
    })

    # Show as clean table with text wrapping
    for _, row in df.iterrows():
        with st.expander(f"📢 {row.get('Symbol', '')} — {row.get('Subject', row.get('Announcement', '')[:60])}"):
            for col, val in row.items():
                if val and str(val).strip():
                    st.markdown(f"**{col}:** {val}")
        st.divider()
