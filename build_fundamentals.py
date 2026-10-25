"""

Pipeline
  1. marketlens.csv -> universe (symbols), Company, Market Cap, Dividend Yield, ML P/E
  2. yfinance (SYMBOL.NS) -> CMP, P/E, P/B, ROE, ROCE, quarterly profit/sales + variances, industry

Run:     python build_fundamentals_v2.py
Resume:  just run again, finished tickers are cached in ./cache/
Test:    set LIMIT = 30 first

pip install yfinance pandas requests
"""
import io
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests
import yfinance as yf

# ============================================================
# SETTINGS
# ============================================================
MARKETLENS_FILE = "marketlens.csv"
UNIVERSE_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
UNIVERSE_LOCAL = "EQUITY_L.csv"          # used only if marketlens.csv is missing
OUTPUT_FILE = "fundamentals.csv"
CACHE_DIR = "cache"
CACHE_MAX_AGE_DAYS = 7                   # re-fetch a ticker only if cache is older
WORKERS = 2                              # low on purpose, yfinance rate-limits
DELAY = 1.0
RETRIES = 4
LIMIT = None                             # e.g. 30 for a test run

CRORE = 1e7

# Paste your industry_normalization dict here (optional).
INDUSTRY_MAP = {}

OUTPUT_COLUMNS = [
    "Company", "CMP Rs.", "P/E", "Mar Cap Rs.Cr.", "Div Yld %",
    "NP Qtr Rs.Cr.", "Qtr Profit Var %", "Sales Qtr Rs.Cr.", "Qtr Sales Var %",
    "ROCE %", "ROE %", "CMP / BV", "Ind PBV", "Symbol", "Industry",
]


# ============================================================
# HELPERS
# ============================================================
def num(x):
    try:
        if x is None or pd.isna(x):
            return None
        return float(x)
    except Exception:
        return None


def clean_number(value):
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return None
    s = str(value).strip().replace(",", "").replace("%", "")
    if s in {"", "-", "--", "NA", "N/A", "nan", "None"}:
        return None
    try:
        return float(s)
    except Exception:
        return None


def row(df, names):
    """Series (index = dates, newest first) for the first matching row label."""
    if df is None or df.empty:
        return None
    for n in names:
        if n in df.index:
            s = df.loc[n].dropna()
            if len(s):
                return s.sort_index(ascending=False)
    return None


# ============================================================
# UNIVERSE (MarketLens first, NSE list as fallback)
# ============================================================
def load_universe():
    if os.path.exists(MARKETLENS_FILE):
        ml = pd.read_csv(MARKETLENS_FILE)
        needed = ["Company", "Market Cap", "PE Ratio", "Dividend Yield (%)"]
        missing = [c for c in needed if c not in ml.columns]
        if missing:
            raise SystemExit(f"marketlens.csv is missing columns: {missing}")

        # "Reliance Industries Limited (RELIANCE)" -> RELIANCE
        ml["Symbol"] = (
            ml["Company"].astype(str).str.extract(r"\(([^()]+)\)\s*$")[0]
            .str.strip().str.upper()
        )
        ml = ml[ml["Symbol"].notna() & (ml["Symbol"] != "")].copy()
        ml = ml.drop_duplicates("Symbol", keep="first")
        ml["Company"] = ml["Company"].astype(str).str.replace(
            r"\s*\([^()]+\)\s*$", "", regex=True).str.strip()
        mc = ml["Market Cap"].map(clean_number)
        ml["ml_mcap_cr"] = mc / CRORE
        ml["ml_pe"] = ml["PE Ratio"].map(clean_number)
        ml["ml_div"] = ml["Dividend Yield (%)"].map(clean_number)
        print(f"Universe from MarketLens: {len(ml)} stocks")
        return ml[["Symbol", "Company", "ml_mcap_cr", "ml_pe", "ml_div"]].reset_index(drop=True)

    # fallback: official NSE list
    try:
        r = requests.get(UNIVERSE_URL,
                         headers={"User-Agent": "Mozilla/5.0", "Accept": "text/csv,*/*"},
                         timeout=30)
        r.raise_for_status()
        text = r.text
    except Exception as e:
        if not os.path.exists(UNIVERSE_LOCAL):
            raise SystemExit(f"No marketlens.csv and could not get NSE list ({e}). "
                             f"Download EQUITY_L.csv and save as {UNIVERSE_LOCAL}")
        text = open(UNIVERSE_LOCAL, encoding="utf-8").read()
    df = pd.read_csv(io.StringIO(text))
    df.columns = [c.strip() for c in df.columns]
    df = df[df["SERIES"].str.strip() == "EQ"].copy()
    df["Symbol"] = df["SYMBOL"].str.strip().str.upper()
    df["Company"] = df["NAME OF COMPANY"].str.strip()
    df["ml_mcap_cr"] = None
    df["ml_pe"] = None
    df["ml_div"] = None
    print(f"Universe from NSE list: {len(df)} stocks")
    return df.drop_duplicates("Symbol")[
        ["Symbol", "Company", "ml_mcap_cr", "ml_pe", "ml_div"]].reset_index(drop=True)


# ============================================================
# FETCH ONE STOCK FROM YFINANCE
# ============================================================
def compute(symbol):
    t = yf.Ticker(f"{symbol}.NS")
    info = t.info or {}

    mcap = num(info.get("marketCap"))
    price = num(info.get("currentPrice") or info.get("regularMarketPrice")
                or info.get("previousClose"))
    if price is None:
        try:
            price = num(t.fast_info.get("last_price"))
        except Exception:
            price = None
    if price is None:
        shares = num(info.get("sharesOutstanding"))
        if mcap and shares:
            price = mcap / shares

    def pct(key):
        v = num(info.get(key))
        return v * 100 if v is not None else None

    pe = num(info.get("trailingPE"))
    pb = num(info.get("priceToBook"))

    out = {
        "Symbol": symbol,
        "yf_price": price,
        "yf_mcap_cr": mcap / CRORE if mcap else None,
        "Industry": info.get("industry"),
        "yf_pe": pe,
        "CMP / BV": pb,
        "Qtr Profit Var %": pct("earningsQuarterlyGrowth"),
        "Qtr Sales Var %": pct("revenueGrowth"),
        "yf_div": num(info.get("dividendYield")),
    }

    # latest quarter profit / sales (crores)
    q = t.quarterly_income_stmt
    q_np = row(q, ["Net Income", "Net Income Common Stockholders"])
    q_sales = row(q, ["Total Revenue", "Operating Revenue"])
    out["NP Qtr Rs.Cr."] = num(q_np.iloc[0]) / CRORE if q_np is not None else None
    out["Sales Qtr Rs.Cr."] = num(q_sales.iloc[0]) / CRORE if q_sales is not None else None

    # statements for ROCE and the ROE fallback
    a = t.income_stmt
    bs = t.balance_sheet
    ebit = row(a, ["EBIT", "Operating Income"])
    assets = row(bs, ["Total Assets"])
    cur_liab = row(bs, ["Current Liabilities", "Total Current Liabilities"])
    equity = row(bs, ["Stockholders Equity", "Common Stock Equity",
                      "Total Equity Gross Minority Interest"])
    a_np = row(a, ["Net Income", "Net Income Common Stockholders"])

    # ROCE (not provided by yfinance) = EBIT / (total assets - current liabilities)
    if ebit is not None and assets is not None and cur_liab is not None:
        cap_emp = num(assets.iloc[0]) - num(cur_liab.iloc[0])
        out["ROCE %"] = (num(ebit.iloc[0]) / cap_emp * 100) if cap_emp and cap_emp > 0 else None
    else:
        out["ROCE %"] = None

    # ROE: yfinance value, else P/B / P/E, else annual NI / equity
    roe = pct("returnOnEquity")
    if roe is None and pe and pb and pe > 0 and pb > 0:
        roe = pb / pe * 100
    if roe is None and a_np is not None and equity is not None:
        e = num(equity.iloc[0])
        if e and e > 0:
            roe = num(a_np.iloc[0]) / e * 100
    out["ROE %"] = roe

    return out


def get_stock(symbol):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{symbol}.json")

    if os.path.exists(path):
        age_days = (time.time() - os.path.getmtime(path)) / 86400
        if age_days <= CACHE_MAX_AGE_DAYS:
            with open(path) as f:
                return json.load(f)

    last_err = None
    for attempt in range(RETRIES):
        try:
            data = compute(symbol)
            with open(path, "w") as f:
                json.dump(data, f)
            time.sleep(DELAY)
            return data
        except Exception as e:
            last_err = e
            msg = str(e).lower()
            if "too many requests" in msg or "rate limit" in msg:
                time.sleep(30 * (attempt + 1))
            else:
                time.sleep(2 * (attempt + 1))

    return {"Symbol": symbol, "_error": str(last_err)}


# ============================================================
# MAIN
# ============================================================
def main():
    universe = load_universe()
    if LIMIT:
        universe = universe.head(LIMIT)
    symbols = universe["Symbol"].tolist()
    print(f"Fetching {len(symbols)} stocks from yfinance...")

    results, done = [], 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(get_stock, s): s for s in symbols}
        for fut in as_completed(futures):
            results.append(fut.result())
            done += 1
            if done % 50 == 0 or done == len(symbols):
                print(f"  {done}/{len(symbols)}")

    yf_df = pd.DataFrame(results)
    errors = int(yf_df["_error"].notna().sum()) if "_error" in yf_df.columns else 0
    df = universe.merge(yf_df, on="Symbol", how="left")

    # ---- final columns: MarketLens for cap/dividend, yfinance for the rest
    df["Mar Cap Rs.Cr."] = df["ml_mcap_cr"].fillna(df.get("yf_mcap_cr"))
    df["Div Yld %"] = df["ml_div"].fillna(df.get("yf_div"))
    df["CMP Rs."] = df.get("yf_price")
    df["P/E"] = df.get("yf_pe")

    # ---- industry + peer-median P/B
    df["Industry"] = df["Industry"].fillna("Unknown").astype(str).str.strip()
    if INDUSTRY_MAP:
        df["Industry"] = df["Industry"].replace(INDUSTRY_MAP)
    valid = df[df["CMP / BV"].notna() & (df["CMP / BV"] > 0)]
    df["Ind PBV"] = df["Industry"].map(valid.groupby("Industry")["CMP / BV"].median())

    # ---- output file
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = None
    out = df[OUTPUT_COLUMNS].sort_values("Mar Cap Rs.Cr.", ascending=False)

    if os.path.exists(OUTPUT_FILE):
        os.replace(OUTPUT_FILE, OUTPUT_FILE + ".backup")
    out.to_csv(OUTPUT_FILE + ".tmp", index=False)
    os.replace(OUTPUT_FILE + ".tmp", OUTPUT_FILE)

    print()
    print(f"Wrote {OUTPUT_FILE}: {len(out)} rows, {errors} failed fetches")
    print()
    print("Missing values per column:")
    print(out.isna().sum().to_string())


if __name__ == "__main__":
    main()