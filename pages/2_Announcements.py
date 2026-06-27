import streamlit as st
import pandas as pd
from nse import NSE
import datetime

st.set_page_config(page_title="Stock Announcements", page_icon="📢", layout="wide")

st.title("📢 Stock Announcements")
st.caption("Search any stock to see latest corporate announcements from NSE")

@st.cache_data
def load_symbols():
    try:
        df = pd.read_csv("nifty500.csv")
        return sorted(df["Symbol"].astype(str).str.strip().tolist())
    except:
        return []

all_symbols = load_symbols()

col1, col2 = st.columns([2, 1])

with col1:
    symbol = st.selectbox(
        "🔍 Search Stock Symbol",
        options=[""] + all_symbols,
        index=0
    )

with col2:
    days = st.slider("Last N days", 1, 30, 7)

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

if symbol:
    with st.spinner(f"Fetching announcements for {symbol}..."):
        try:
            nse = NSE()
            to_date = datetime.date.today()
            from_date = to_date - datetime.timedelta(days=days)
            data = nse.announcements(
                index="equities",
                symbol=symbol,
                from_date=datetime.datetime.combine(from_date, datetime.time()),
                to_date=datetime.datetime.combine(to_date, datetime.time())
            )
            nse.exit()

            if not data:
                st.warning(f"No announcements found for {symbol} in last {days} days!")
            else:
                df = pd.DataFrame(data)
                st.success(f"Found {len(df)} announcements for **{symbol}** in last {days} days!")

                # Show clean columns
                show_cols = [c for c in ["symbol", "desc", "attchmntText", "sort_date", "exchdisstime"] if c in df.columns]
                df = df[show_cols].rename(columns={
                    "symbol": "Symbol",
                    "desc": "Subject",
                    "attchmntText": "Details",
                    "sort_date": "Date",
                    "exchdisstime": "Time"
                })
                st.dataframe(df, use_container_width=True)

        except Exception as e:
            st.error(f"Error fetching data: {e}")
