import datetime
from pathlib import Path
import yfinance as yf
import plotly.graph_objects as go

import pandas as pd
import requests
import streamlit as st

DATA_DIR = Path(".")
LOCAL_FILE = DATA_DIR / "sec_bhavdata_latest.csv"
FALLBACK_FILE = DATA_DIR / "sec_bhavdata_full_02062026.csv"
NSE_BASE_URL = "https://nsearchives.nseindia.com/products/content"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer": "https://www.nseindia.com/",
}
MAX_LOOKBACK_DAYS = 7
STALE_HOURS = 24


def build_bhavcopy_url(date: datetime.date) -> str:
    return f"{NSE_BASE_URL}/sec_bhavdata_full_{date.strftime('%d%m%Y')}.csv"


def get_candidate_dates() -> list[datetime.date]:
    today = datetime.date.today()
    return [today - datetime.timedelta(days=i) for i in range(MAX_LOOKBACK_DAYS)]


def download_bhavcopy_content(date: datetime.date) -> bytes:
    url = build_bhavcopy_url(date)
    response = requests.get(url, headers=HEADERS, timeout=60)
    if response.status_code == 200 and len(response.content) > 200:
        return response.content
    raise RuntimeError(f"No valid data for {date} (status {response.status_code})")


def save_latest_csv(content: bytes) -> None:
    LOCAL_FILE.write_bytes(content)


def is_file_stale(path: Path) -> bool:
    if not path.exists():
        return True
    age = datetime.datetime.now() - datetime.datetime.fromtimestamp(path.stat().st_mtime)
    return age >= datetime.timedelta(hours=STALE_HOURS)


@st.cache_data
def load_dataframe(path: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    if "DATE1" in df.columns:
        df["DATE1"] = pd.to_datetime(
            df["DATE1"],
            errors="coerce",
            dayfirst=True
        ).dt.strftime("%d-%b-%Y")
    if "DELIV_PER" in df.columns:
        df["DELIV_PER"] = pd.to_numeric(df["DELIV_PER"], errors="coerce")
    if "TTL_TRD_QNTY" in df.columns:
        df["TTL_TRD_QNTY"] = pd.to_numeric(df["TTL_TRD_QNTY"], errors="coerce")


    if "DELIV_PER" in df.columns:
        df = df[df["DELIV_PER"].notna()]

    return df


def get_data() -> tuple[pd.DataFrame, dict]:
    source_info: dict = {
        "source_path": None,
        "source_date": None,
        "status": None,
        "message": None,
    }

    if is_file_stale(LOCAL_FILE):
        for candidate_date in get_candidate_dates():
            try:
                content = download_bhavcopy_content(candidate_date)
                save_latest_csv(content)
                source_info["source_path"] = str(LOCAL_FILE)
                source_info["source_date"] = candidate_date
                source_info["status"] = "downloaded"
                source_info["message"] = f"Downloaded latest available bhavcopy for {candidate_date:%Y-%m-%d}."
                break
            except Exception:
                continue
        else:
            source_info["status"] = "download_failed"
            source_info["message"] = "Could not download today's bhavcopy. Using the last available local copy or fallback data."

    if LOCAL_FILE.exists():
        path = LOCAL_FILE
        source_info.setdefault("source_path", str(path))
        source_info.setdefault("source_date", datetime.date.fromtimestamp(path.stat().st_mtime))
        source_info.setdefault("status", "cached")
        df = load_dataframe(str(path), path.stat().st_mtime)
        return df, source_info

    if FALLBACK_FILE.exists():
        path = FALLBACK_FILE
        source_info["source_path"] = str(path)
        source_info["source_date"] = None
        source_info["status"] = "fallback"
        source_info["message"] = "Loaded sample fallback data because no downloaded copy is available."
        df = load_dataframe(str(path), path.stat().st_mtime)
        return df, source_info

    raise FileNotFoundError(
        "No bhavcopy data file is available. Please run the download script or place a CSV file in the workspace."
    )


def main() -> None:
    st.set_page_config(
        page_title="NSE Delivery Dashboard",
        page_icon="📈",
        layout="wide"
    )

    st.markdown(
        '<meta name="google-site-verification" content="<meta name="google-site-verification" content="MukO9SuxySRVLRS6Qx7UpHuwXOgnrw9uRvdZJiFFyAY" />" />',
        unsafe_allow_html=True

    )

    st.title("📈 NSE Delivery Dashboard")
    st.caption("Live NSE bhavcopy data — updates daily automatically")

    if st.button("🔄 Refresh Data"):
        if LOCAL_FILE.exists():
            LOCAL_FILE.unlink()
        st.rerun()

    timeframe = st.radio(
        "Average Volume Period",
        ["1D", "1W", "1M", "3M"],
        horizontal=True
    )

    df, source_info = get_data()

    file_map = {
        "1D": "avg_volume_1d.csv",
        "1W": "avg_volume_1w.csv",
        "1M": "avg_volume_1m.csv",
        "3M": "avg_volume_3m.csv",
    }

    avg_volume = pd.read_csv(file_map[timeframe])
    df = df.merge(avg_volume, on="SYMBOL", how="left")

    if timeframe == "1D":
        df["AVG_30D_VOLUME"] = df["TTL_TRD_QNTY"]

    df["VOL_RATIO"] = (
        df["TTL_TRD_QNTY"] / df["AVG_30D_VOLUME"]
    ).round(2)

    # ── Status banner ──────────────────────────────────────────
    if source_info["status"] == "downloaded":
        st.success(source_info["message"])
    elif source_info["status"] == "cached":
        st.info(f"Using cached data from {source_info['source_date']:%Y-%m-%d}.")
    elif source_info["status"] == "download_failed":
        st.warning(source_info["message"])
    elif source_info["status"] == "fallback":
        st.warning(source_info["message"])

    # ── Metric cards ───────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Stocks", len(df))
    col2.metric("Avg Delivery %", f"{df['DELIV_PER'].mean():.1f}%")
    col3.metric("Avg Vol Ratio", f"{df['VOL_RATIO'].mean():.2f}x")
    col4.metric("Data Date", str(source_info["source_date"]))

    st.divider()

    # ── Filters ────────────────────────────────────────────────
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        all_symbols = df["SYMBOL"].dropna().unique().tolist()
        search = st.selectbox(
            "🔍 Search Symbol",
            options=[""] + sorted(all_symbols),
            index=0
        )
    with col_b:
        index_filter = st.selectbox("Index Filter", ["All Stocks", "NIFTY 500"])
    with col_c:
        min_delivery = st.slider("Minimum Delivery %", 0, 100, 70)

    col_d, col_e = st.columns(2)
    with col_d:
        sort_by = st.selectbox("Sort by", ["DELIV_PER", "VOL_RATIO", "AVG_30D_VOLUME", "TTL_TRD_QNTY", "SYMBOL"])
    with col_e:
        order = st.radio("Sort order", ["Descending", "Ascending"], horizontal=True)

    # ── Apply filters ──────────────────────────────────────────
    if search:
        df = df[df["SYMBOL"] == search]

    if index_filter == "NIFTY 500":
        nifty500 = pd.read_csv("nifty500.csv")
        symbols = nifty500["Symbol"].astype(str).str.strip().tolist()
        df = df[df["SYMBOL"].isin(symbols)]

    df = df[df["DELIV_PER"] >= min_delivery]

    ascending = order == "Ascending"
    if sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=ascending)

    display_df = df.copy().rename(columns={"AVG_30D_VOLUME": f"AVG_{timeframe}_VOLUME"})

    display_columns = [
        col for col in [
            "DATE1", "SYMBOL", "DELIV_PER",
            "TTL_TRD_QNTY", f"AVG_{timeframe}_VOLUME",
            "VOL_RATIO", "OPEN_PRICE", "CLOSE_PRICE",
        ] if col in display_df.columns
    ]

    display_df = display_df[display_columns].reset_index(drop=True)

    # ── Color coding ───────────────────────────────────────────
    def color_deliv(val):
        if val >= 80:
            return "background-color: #1a4a2e; color: #00C897"
        elif val >= 60:
            return "background-color: #2a3a1a; color: #90EE90"
        else:
            return "background-color: #4a1a1a; color: #FF6B6B"

    def color_ratio(val):
        if val >= 2:
            return "background-color: #1a3a4a; color: #00BFFF"
        elif val >= 1:
            return "background-color: #1a2a3a; color: #87CEEB"
        else:
            return "background-color: #3a2a1a; color: #FFA500"

    styled = display_df.style
    if "DELIV_PER" in display_df.columns:
        styled = styled.map(color_deliv, subset=["DELIV_PER"])
    if "VOL_RATIO" in display_df.columns:
        styled = styled.map(color_ratio, subset=["VOL_RATIO"])

    st.dataframe(styled, use_container_width=True)


    st.caption(f"Showing {len(display_df)} stocks · Source: `{source_info['source_path']}`")


if __name__ == "__main__":
    main()