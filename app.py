import datetime
from pathlib import Path

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

    try:
        file_map = {
            "1D": "avg_volume_1d.csv",
            "1W": "avg_volume_1w.csv",
            "1M": "avg_volume_1m.csv",
            "3M": "avg_volume_3m.csv",
        }

        avg_volume = pd.read_csv(
            file_map[timeframe]
        )

        df = df.merge(
            avg_volume,
            on="SYMBOL",
            how="left"
        )

        df["VOL_RATIO"] = (
            df["TTL_TRD_QNTY"] /
            df["AVG_30D_VOLUME"]
        ).round(2)

    except Exception as e:
        st.error(f"Could not load avg_volume.csv: {e}")
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
    st.title("NSE Delivery Dashboard")
    st.write(
        "This dashboard updates daily from NSE archives and shows delivery data in sorted order."
    )

    if st.button("Refresh data now"):
        if LOCAL_FILE.exists():
            LOCAL_FILE.unlink()
        st.rerun()

    df, source_info = get_data()
    

    st.write(df.columns.tolist())
    if source_info["status"] == "downloaded":
        st.success(source_info["message"])
    elif source_info["status"] == "cached":
        st.info(f"Using cached data from {source_info['source_date']:%Y-%m-%d}.")
    elif source_info["status"] == "download_failed":
        st.warning(source_info["message"])
    elif source_info["status"] == "fallback":
        st.warning(source_info["message"])

    st.markdown(
        f"**Data source:** `{source_info['source_path']}`"
    )

    search = st.text_input("Search Stock symbol")

    timeframe = st.radio(
        "Timeframe",
        ["1D", "1W", "1M", "3M"],
        horizontal=True
)

    index_filter = st.selectbox(
        "Index Filter",
        ["All Stocks", "NIFTY 500"]
    )
    
    min_delivery = st.slider("Minimum Delivery %", 0, 100, 70)
    sort_by = st.selectbox(
        "Sort by",
        [
            "DELIV_PER",
            "VOL_RATIO",
            "AVG_30D_VOLUME",
            "TTL_TRD_QNTY",
            "SYMBOL",
        ],
        index=0,
    )
    order = st.radio("Sort order", ["Descending", "Ascending"], index=0)

    if search:
        df = df[df["SYMBOL"].str.contains(search.upper(), na=False)]

    if index_filter == "NIFTY 500":
        nifty500 = pd.read_csv("nifty500.csv")

        symbols = (
            nifty500["Symbol"]
            .astype(str)
            .str.strip()
            .tolist()
        )

        df = df[df["SYMBOL"].isin(symbols)]

    df = df[df["DELIV_PER"] >= min_delivery]

    ascending = order == "Ascending"
    if sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=ascending)

    display_columns = [
        col
        for col in [
            "DATE1",
            "SYMBOL",
            "DELIV_PER",
            "TTL_TRD_QNTY",
            "AVG_30D_VOLUME",
            "VOL_RATIO",
            "OPEN_PRICE",
            "CLOSE_PRICE",
        ]
        if col in df.columns
    ]

    st.dataframe(df[display_columns].reset_index(drop=True))


if __name__ == "__main__":
    main()
