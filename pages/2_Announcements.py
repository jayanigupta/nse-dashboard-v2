import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Stock Announcements", page_icon="📢", layout="wide")

st.title("📢 Stock Announcements")
st.caption("Search any stock to see latest corporate announcements from NSE")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer": "https://www.nseindia.com/",
    "Accept": "application/json",
}

@st.cache_data(ttl=1800)
def fetch_announcements(symbol):
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
    response = session.get(
        f"https://www.nseindia.com/api/corp-info?symbol={symbol}&corpType=announcements",
        headers=HEADERS,
        timeout=15
    )
    if response.status_code == 200:
        return response.json()
    return None

# Load symbols for autocomplete
@st.cache_data
def load_symbols():
    try:
        df = pd.read_csv("nifty500.csv")
        return sorted(df["Symbol"].astype(str).str.strip().tolist())
    except:
        return []

all_symbols = load_symbols()

# Search box
symbol = st.selectbox(
    "🔍 Search Stock Symbol",
    options=[""] + all_symbols,
    index=0
)

if symbol:
    with st.spinner(f"Fetching announcements for {symbol}..."):
        data = fetch_announcements(symbol)

    if not data:
        st.warning(f"No announcements found for {symbol} — try another stock!")
    else:
        # NSE returns data in different formats
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Try common keys
            for key in ["data", "announcements", "results", "corpInfo"]:
                if key in data:
                    df = pd.DataFrame(data[key])
                    break
            else:
                df = pd.DataFrame([data])

        if df.empty:
            st.warning("No announcements data available!")
        else:
            st.success(f"Found {len(df)} announcements for {symbol}!")
            st.dataframe(df, use_container_width=True)
