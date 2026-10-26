
"""
Build fundamentals.csv from MarketLens universe + Yahoo Finance data.

Pipeline:
  1. marketlens.csv -> universe, company, market cap, dividend yield, ML P/E
  2. yfinance (SYMBOL.NS) -> CMP, P/E, P/B, ROE, ROCE,
     quarterly profit/sales + growth, industry

Run:     python build_fundamentals_v2.py
Resume:  rerun; completed tickers are cached in ./cache/
Test:    LIMIT = 30

Install:
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
UNIVERSE_URL = (
    "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
)
UNIVERSE_LOCAL = "EQUITY_L.csv"
OUTPUT_FILE = "fundamentals.csv"
CACHE_DIR = "cache"

CACHE_MAX_AGE_DAYS = 7
WORKERS = 2
DELAY = 1.0
RETRIES = 4
LIMIT = None  # Keep at 30 until the results are verified

CRORE = 1e7

INDUSTRY_MAP = {}

OUTPUT_COLUMNS = [
    "Company",
    "CMP Rs.",
    "P/E",
    "Mar Cap Rs.Cr.",
    "Div Yld %",
    "NP Qtr Rs.Cr.",
    "Qtr Profit Var %",
    "Sales Qtr Rs.Cr.",
    "Qtr Sales Var %",
    "ROCE %",
    "ROE %",
    "CMP / BV",
    "Ind PBV",
    "Symbol",
    "Industry",
]


# ============================================================
# HELPERS
# ============================================================

def num(value):
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def clean_number(value):
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    text = str(value).strip().replace(",", "").replace("%", "")

    if text.lower() in {"", "-", "--", "na", "n/a", "nan", "none"}:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def normalize_label(label):
    """Normalize financial statement row labels for matching."""
    return re.sub(r"[^a-z0-9]", "", str(label).lower())


def row(df, names):
    """
    Return the newest available series for a matching statement row.

    Matching ignores spaces, punctuation and capitalization.
    """
    if df is None or df.empty:
        return None

    label_map = {
        normalize_label(label): label
        for label in df.index
    }

    for name in names:
        actual_label = label_map.get(normalize_label(name))

        if actual_label is None:
            continue

        values = df.loc[actual_label]

        if isinstance(values, pd.DataFrame):
            values = values.iloc[0]

        values = values.dropna()

        if not values.empty:
            return values.sort_index(ascending=False)

    return None


def latest_value(series):
    """Get the newest numeric value, including zero or negative values."""
    if series is None or series.empty:
        return None

    for value in series:
        value = num(value)
        if value is not None:
            return value

    return None


def statement_value(df, labels):
    """Find a row and return its newest numeric value."""
    return latest_value(row(df, labels))


def get_statement(ticker, attribute):
    """Return a statement DataFrame without failing the whole stock."""
    try:
        result = getattr(ticker, attribute)
        if isinstance(result, pd.DataFrame):
            return result
    except Exception:
        pass

    return pd.DataFrame()


# ============================================================
# UNIVERSE
# ============================================================

def load_universe():
    if os.path.exists(MARKETLENS_FILE):
        ml = pd.read_csv(MARKETLENS_FILE)

        needed = [
            "Company",
            "Market Cap",
            "PE Ratio",
            "Dividend Yield (%)",
        ]

        missing = [column for column in needed if column not in ml.columns]
        if missing:
            raise SystemExit(
                f"marketlens.csv is missing columns: {missing}"
            )

        # Example: "Reliance Industries Limited (RELIANCE)" -> RELIANCE
        ml["Symbol"] = (
            ml["Company"]
            .astype(str)
            .str.extract(r"\(([^()]+)\)\s*$")[0]
            .str.strip()
            .str.upper()
        )

        ml = ml[
            ml["Symbol"].notna() & (ml["Symbol"] != "")
        ].copy()

        ml = ml.drop_duplicates("Symbol", keep="first")

        ml["Company"] = (
            ml["Company"]
            .astype(str)
            .str.replace(r"\s*\([^()]+\)\s*$", "", regex=True)
            .str.strip()
        )

        market_cap = ml["Market Cap"].map(clean_number)
        ml["ml_mcap_cr"] = market_cap / CRORE
        ml["ml_pe"] = ml["PE Ratio"].map(clean_number)
        ml["ml_div"] = ml["Dividend Yield (%)"].map(clean_number)

        print(f"Universe from MarketLens: {len(ml)} stocks")

        return ml[
            ["Symbol", "Company", "ml_mcap_cr", "ml_pe", "ml_div"]
        ].reset_index(drop=True)

    # Fallback: official NSE equity list
    try:
        response = requests.get(
            UNIVERSE_URL,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/csv,*/*",
            },
            timeout=30,
        )
        response.raise_for_status()
        csv_text = response.text

    except Exception as exc:
        if not os.path.exists(UNIVERSE_LOCAL):
            raise SystemExit(
                f"No marketlens.csv and could not download NSE list: {exc}. "
                f"Download EQUITY_L.csv and save it as {UNIVERSE_LOCAL}"
            )

        with open(UNIVERSE_LOCAL, encoding="utf-8") as file:
            csv_text = file.read()

    df = pd.read_csv(io.StringIO(csv_text))
    df.columns = [column.strip() for column in df.columns]

    df = df[df["SERIES"].astype(str).str.strip() == "EQ"].copy()
    df["Symbol"] = df["SYMBOL"].astype(str).str.strip().str.upper()
    df["Company"] = df["NAME OF COMPANY"].astype(str).str.strip()

    df["ml_mcap_cr"] = None
    df["ml_pe"] = None
    df["ml_div"] = None

    print(f"Universe from NSE list: {len(df)} stocks")

    return df.drop_duplicates("Symbol")[
        ["Symbol", "Company", "ml_mcap_cr", "ml_pe", "ml_div"]
    ].reset_index(drop=True)


# ============================================================
# FETCH ONE STOCK FROM YFINANCE
# ============================================================

def compute(symbol):
    ticker = yf.Ticker(f"{symbol}.NS")
    info = ticker.info or {}

    market_cap = num(info.get("marketCap"))

    price = num(
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("previousClose")
    )

    if price is None:
        try:
            price = num(ticker.fast_info.get("last_price"))
        except Exception:
            pass

    if price is None:
        shares = num(info.get("sharesOutstanding"))
        if market_cap and shares:
            price = market_cap / shares

    def pct(key):
        value = num(info.get(key))
        return value * 100 if value is not None else None


    pe = num(info.get("trailingPE"))
    pb = num(info.get("priceToBook"))

    out = {
        "Symbol": symbol,
        "yf_price": price,
        "yf_mcap_cr": market_cap / CRORE if market_cap else None,
        "Industry": info.get("industry"),
        "yf_pe": pe,
        "CMP / BV": pb,
        "Qtr Profit Var %": pct("earningsQuarterlyGrowth"),
        "Qtr Sales Var %": pct("revenueGrowth"),
        # Keep the current corrected dividend-yield handling.
        "yf_div": num(info.get("dividendYield")),
    }

    # Quarterly profit and sales
    quarterly = get_statement(ticker, "quarterly_income_stmt")

    quarter_profit = row(
        quarterly,
        ["Net Income", "Net Income Common Stockholders"],
    )
    quarter_sales = row(
        quarterly,
        ["Total Revenue", "Operating Revenue"],
    )

    profit_value = latest_value(quarter_profit)
    sales_value = latest_value(quarter_sales)

    out["NP Qtr Rs.Cr."] = (
        profit_value / CRORE if profit_value is not None else None
    )
    out["Sales Qtr Rs.Cr."] = (
        sales_value / CRORE if sales_value is not None else None
    )

    # Annual financial statements
    income = get_statement(ticker, "income_stmt")
    balance = get_statement(ticker, "balance_sheet")

    ebit = statement_value(
        income,
        [
            "EBIT",
            "Operating Income",
            "Ebit",
            "Normalized EBITDA",
        ],
    )

    assets = statement_value(
        balance,
        ["Total Assets"],
    )

    current_liabilities = statement_value(
        balance,
        [
            "Current Liabilities",
            "Total Current Liabilities",
            "Current Liabilities And Provisions",
        ],
    )

    equity = statement_value(
        balance,
        [
            "Stockholders Equity",
            "Common Stock Equity",
            "Total Equity Gross Minority Interest",
            "Total Stockholder Equity",
        ],
    )

    net_income = statement_value(
        income,
        ["Net Income", "Net Income Common Stockholders"],
    )

    # ROCE = EBIT / Capital Employed * 100.
    # Capital employed = total assets - current liabilities.
    roce = None

    if (
        ebit is not None
        and assets is not None
        and current_liabilities is not None
    ):
        capital_employed = assets - current_liabilities

        if capital_employed > 0:
            roce = ebit / capital_employed * 100

    out["ROCE %"] = roce

    # ROE: Yahoo value, then P/B divided by P/E, then net income / equity.
    roe = pct("returnOnEquity")

    if roe is None and pe is not None and pb is not None and pe > 0 and pb > 0:
        roe = pb / pe * 100

    if roe is None and net_income is not None and equity is not None and equity > 0:
        roe = net_income / equity * 100

    out["ROE %"] = roe

    # Internal diagnostics, not written to the final CSV.
    if roce is None:
        missing = []

        if ebit is None:
            missing.append("EBIT")
        if assets is None:
            missing.append("Total Assets")
        if current_liabilities is None:
            missing.append("Current Liabilities")

        out["_roce_issue"] = ", ".join(missing) or "Invalid capital employed"
    else:
        out["_roce_issue"] = None

    # Important: return the completed stock record.
    return out


# ============================================================
# CACHE AND RETRIES
# ============================================================

def get_stock(symbol):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"{symbol}.json")

    if os.path.exists(path):
        age_days = (time.time() - os.path.getmtime(path)) / 86400

        if age_days <= CACHE_MAX_AGE_DAYS:
            try:
                with open(path, encoding="utf-8") as file:
                    cached = json.load(file)

                # Reuse only valid records with ROCE diagnostics.
                # Old cached records are refreshed once by this version.
                if (
                    isinstance(cached, dict)
                    and "ROCE %" in cached
                    and "_roce_issue" in cached
                ):
                    return cached

            except (OSError, json.JSONDecodeError):
                pass

    last_error = None

    for attempt in range(RETRIES):
        try:
            data = compute(symbol)

            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file)

            time.sleep(DELAY)
            return data

        except Exception as exc:
            last_error = exc
            message = str(exc).lower()

            if "too many requests" in message or "rate limit" in message:
                time.sleep(30 * (attempt + 1))
            else:
                time.sleep(2 * (attempt + 1))

    return {
        "Symbol": symbol,
        "_error": str(last_error),
        "_roce_issue": "Fetch failed",
    }


# ============================================================
# MAIN
# ============================================================

def main():
    universe = load_universe()

    if LIMIT:
        universe = universe.head(LIMIT)

    symbols = universe["Symbol"].tolist()
    print(f"Fetching {len(symbols)} stocks from yfinance...")

    results = []
    done = 0

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(get_stock, symbol): symbol
            for symbol in symbols
        }

        for future in as_completed(futures):
            symbol = futures[future]

            try:
                results.append(future.result())
            except Exception as exc:
                results.append({
                    "Symbol": symbol,
                    "_error": str(exc),
                    "_roce_issue": "Fetch failed",
                })

            done += 1

            if done % 50 == 0 or done == len(symbols):
                print(f"  {done}/{len(symbols)}")

    yahoo_df = pd.DataFrame(results)

    errors = (
        int(yahoo_df["_error"].notna().sum())
        if "_error" in yahoo_df.columns
        else 0
    )

    df = universe.merge(yahoo_df, on="Symbol", how="left")

    # Market capitalization: MarketLens first, Yahoo fallback.
    df["Mar Cap Rs.Cr."] = df["ml_mcap_cr"].fillna(
        df.get("yf_mcap_cr")
    )

    # Preserve corrected dividend-yield handling.
    if "yf_div" in df.columns:
        df["Div Yld %"] = pd.to_numeric(df["yf_div"], errors="coerce")
    else:
        df["Div Yld %"] = None

    df["CMP Rs."] = df.get("yf_price")
    df["P/E"] = df.get("yf_pe")

    # Industry and industry median P/B.
    df["Industry"] = (
        df["Industry"].fillna("Unknown").astype(str).str.strip()
    )

    if INDUSTRY_MAP:
        df["Industry"] = df["Industry"].replace(INDUSTRY_MAP)

    valid_pb = df[
        df["CMP / BV"].notna() & (df["CMP / BV"] > 0)
    ]

    industry_medians = valid_pb.groupby("Industry")["CMP / BV"].median()
    df["Ind PBV"] = df["Industry"].map(industry_medians)

    # Ensure all expected output columns exist.
    for column in OUTPUT_COLUMNS:
        if column not in df.columns:
            df[column] = None

    output = df[OUTPUT_COLUMNS].sort_values(
        "Mar Cap Rs.Cr.",
        ascending=False,
    )

    # Save atomically and retain the previous output as a backup.
    if os.path.exists(OUTPUT_FILE):
        os.replace(OUTPUT_FILE, OUTPUT_FILE + ".backup")

    output.to_csv(OUTPUT_FILE + ".tmp", index=False)
    os.replace(OUTPUT_FILE + ".tmp", OUTPUT_FILE)

    print()
    print(f"Wrote {OUTPUT_FILE}: {len(output)} rows, {errors} failed fetches")
    print()
    print("Missing values per column:")
    print(output.isna().sum().to_string())

    # Explain why ROCE is missing, without adding debug columns to the CSV.
    if "_roce_issue" in df.columns:
        issues = df.loc[
            df["ROCE %"].isna(),
            ["Symbol", "_roce_issue"],
        ].copy()


if __name__ == "__main__":
    main()
