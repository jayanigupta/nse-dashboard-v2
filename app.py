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
def load_data(path: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()

    if "DATE1" in df.columns:
        df["DATE1"] = pd.to_datetime(df["DATE1"], errors="coerce", dayfirst=True)

    if "DELIV_PER" in df.columns:
        df["DELIV_PER"] = pd.to_numeric(df["DELIV_PER"], errors="coerce")

    if "TTL_TRD_QNTY" in df.columns:
        df["TTL_TRD_QNTY"] = pd.to_numeric(df["TTL_TRD_QNTY"], errors="coerce")

    return df


def get_data() -> tuple[pd.DataFrame, dict]:
    source_info = {
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
                source_info["message"] = f"Downloaded latest bhavcopy {candidate_date:%Y-%m-%d}"
                break
            except Exception:
                continue
        else:
            source_info["status"] = "download_failed"
            source_info["message"] = "Using last available data"

    if LOCAL_FILE.exists():
        path = LOCAL_FILE
        df = load_data(str(path), path.stat().st_mtime)
        source_info["source_path"] = str(path)
        source_info["source_date"] = datetime.date.fromtimestamp(path.stat().st_mtime)
        source_info["status"] = "cached"
        return df, source_info

    if FALLBACK_FILE.exists():
        path = FALLBACK_FILE
        df = load_data(str(path), path.stat().st_mtime)
        source_info["source_path"] = str(path)
        source_info["status"] = "fallback"
        return df, source_info

    raise FileNotFoundError("No data available")


def main():
    st.title("NSE Delivery Dashboard")

    df, source_info = get_data()

    # ---------------- FIX: safe VOL_RATIO ----------------
    if "AVG_30D_VOLUME" in df.columns and "TTL_TRD_QNTY" in df.columns:
        df["VOL_RATIO"] = (
            df["TTL_TRD_QNTY"] / df["AVG_30D_VOLUME"].replace(0, None)
        ).round(2)
    else:
        df["VOL_RATIO"] = None

    # ---------------- 30D spike logic ----------------
    df_analytics = df.copy()

    df_analytics["DATE1"] = pd.to_datetime(df_analytics["DATE1"], errors="coerce")
    df_analytics = df_analytics[df_analytics["DATE1"].notna()]

    if not df_analytics.empty:
        latest_date = df_analytics["DATE1"].max()
        start_30d = latest_date - pd.Timedelta(days=30)

        df_30d = df_analytics[df_analytics["DATE1"] >= start_30d]
        today_df = df_analytics[df_analytics["DATE1"] == latest_date]

        avg_30d = (
            df_30d.groupby("SYMBOL")["TTL_TRD_QNTY"]
            .mean()
            .reset_index()
            .rename(columns={"TTL_TRD_QNTY": "AVG_30D_VOLUME"})
        )

        today_vol = (
            today_df.groupby("SYMBOL")["TTL_TRD_QNTY"]
            .sum()
            .reset_index()
            .rename(columns={"TTL_TRD_QNTY": "TODAY_VOLUME"})
        )

        merged = pd.merge(avg_30d, today_vol, on="SYMBOL", how="inner")

        merged["VOLUME_SPIKE_%"] = (
            (merged["TODAY_VOLUME"] - merged["AVG_30D_VOLUME"])
            / merged["AVG_30D_VOLUME"].replace(0, None)
        ) * 100

        top_10_spikes = merged.sort_values(
            "VOLUME_SPIKE_%",
            ascending=False
        ).head(10)
    else:
        top_10_spikes = pd.DataFrame()

    # ---------------- UI ----------------
    st.subheader("🔥 Top 10 Volume Spike Stocks")

    if not top_10_spikes.empty:
        st.dataframe(
            top_10_spikes[
                ["SYMBOL", "TODAY_VOLUME", "AVG_30D_VOLUME", "VOLUME_SPIKE_%"]
            ],
            use_container_width=True
        )

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
