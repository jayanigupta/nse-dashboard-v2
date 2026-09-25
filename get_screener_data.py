import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import StringIO
import os
import glob
import yfinance as yf


# ============================================================
# SETTINGS
# ============================================================

BASE_URL = "https://www.screener.in/screens/508045/price-to-book-ratio/"

NIFTY_FOLDER = "nse_industry_data"


# ============================================================
# PART 1 — LOAD EXISTING NIFTY INDUSTRY DATA
# ============================================================

print()
print("===================================")
print("Loading existing Industry data")
print("===================================")
print()

industry_tables = []

for filepath in glob.glob(
    os.path.join(
        NIFTY_FOLDER,
        "*.csv"
    )
):

    try:

        nifty_df = pd.read_csv(filepath)

        nifty_df.columns = (
            nifty_df.columns
            .str.strip()
            .str.replace(
                r"\s+",
                " ",
                regex=True
            )
        )

        if (
            "Symbol" in nifty_df.columns
            and
            "Industry" in nifty_df.columns
        ):

            temp = nifty_df[
                ["Symbol", "Industry"]
            ].copy()

            temp["Symbol"] = (
                temp["Symbol"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            temp["Industry"] = (
                temp["Industry"]
                .astype(str)
                .str.strip()
            )

            industry_tables.append(temp)

    except Exception as e:

        print(
            f"Could not read {filepath}: {e}"
        )


if industry_tables:

    industry_mapping = pd.concat(
        industry_tables,
        ignore_index=True
    )

    industry_mapping = (
        industry_mapping
        .drop_duplicates(
            subset=["Symbol"],
            keep="first"
        )
    )

else:

    industry_mapping = pd.DataFrame(
        columns=[
            "Symbol",
            "Industry"
        ]
    )


print(
    f"Loaded {len(industry_mapping)} "
    f"Symbol → Industry mappings"
)


# ============================================================
# PART 2 — SCRAPE SCREENER
# ============================================================

print()
print("===================================")
print("Fetching Screener pages")
print("===================================")
print()

all_data = []

headers = {
    "User-Agent": "Mozilla/5.0"
}


for page in range(1, 20):

    print(
        f"Fetching page {page}/19..."
    )

    url = f"{BASE_URL}?page={page}"

    response = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()


    # ========================================================
    # EXTRACT SYMBOLS
    # ========================================================

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    symbols = []

    for row in soup.find_all(
        "tr",
        attrs={
            "data-row-company-id": True
        }
    ):

        link = row.find(
            "a",
            href=lambda x:
                x and "/company/" in x
        )

        if link:

            href = link.get(
                "href",
                ""
            )

            parts = (
                href
                .strip("/")
                .split("/")
            )

            try:

                company_index = (
                    parts.index("company")
                )

                symbol = (
                    parts[
                        company_index + 1
                    ]
                )

                symbols.append(
                    symbol.upper()
                )

            except (
                ValueError,
                IndexError
            ):

                symbols.append(None)

        else:

            symbols.append(None)


    # ========================================================
    # EXTRACT TABLE
    # ========================================================

    tables = pd.read_html(
        StringIO(response.text)
    )

    if not tables:

        print(
            f"No table found on page {page}"
        )

        continue


    df = tables[0]


    # Remove repeated header rows
    if "S.No." in df.columns:

        df = df[
            df["S.No."]
            .astype(str)
            != "S.No."
        ].copy()


    # ========================================================
    # ADD SYMBOL
    # ========================================================

    if len(symbols) == len(df):

        df["Symbol"] = symbols

    else:

        print(
            f"WARNING page {page}: "
            f"{len(df)} table rows vs "
            f"{len(symbols)} symbols"
        )

        df["Symbol"] = None


    all_data.append(df)

    print(
        f"  → {len(df)} companies"
    )


# ============================================================
# PART 3 — COMBINE
# ============================================================

final_df = pd.concat(
    all_data,
    ignore_index=True
)

final_df = final_df.drop_duplicates()


final_df["Symbol"] = (
    final_df["Symbol"]
    .astype(str)
    .str.strip()
    .str.upper()
)


# ============================================================
# PART 4 — ADD EXISTING NIFTY INDUSTRIES
# ============================================================

final_df = final_df.merge(
    industry_mapping,
    on="Symbol",
    how="left"
)


# ============================================================
# PART 5 — YFINANCE FOR MISSING INDUSTRIES
# ============================================================

print()
print("===================================")
print("Finding remaining Industries")
print("Using yfinance")
print("===================================")
print()


missing_mask = (
    final_df["Industry"].isna()
    |
    final_df["Industry"].astype(str).isin(
        ["", "nan", "None"]
    )
)


missing_symbols = (
    final_df.loc[
        missing_mask,
        "Symbol"
    ]
    .dropna()
    .unique()
)


print(
    f"Industries still missing: "
    f"{len(missing_symbols)}"
)

print()


for i, symbol in enumerate(
    missing_symbols,
    start=1
):

    # Ignore numeric BSE-style codes
    if str(symbol).isdigit():

        print(
            f"[{i}/{len(missing_symbols)}] "
            f"{symbol} → skipped "
            f"(numeric symbol)"
        )

        continue


    print(
        f"[{i}/{len(missing_symbols)}] "
        f"{symbol}"
    )


    try:

        ticker = yf.Ticker(
            f"{symbol}.NS"
        )

        info = ticker.info

        industry = info.get(
            "industry"
        )


        if industry:

            final_df.loc[
                final_df["Symbol"] == symbol,
                "Industry"
            ] = industry

            print(
                f"  ✓ {industry}"
            )

        else:

            print(
                "  → Industry not found"
            )


    except Exception as e:

        print(
            f"  → Error: {e}"
        )


# ============================================================
# PART 6 — SAVE
# ============================================================

final_df.to_csv(
    "fundamentals.csv",
    index=False
)


# ============================================================
# FINAL SUMMARY
# ============================================================

industry_found = (
    final_df["Industry"]
    .notna()
    .sum()
)

industry_missing = (
    final_df["Industry"]
    .isna()
    .sum()
)


print()
print("===================================")
print("FINAL RESULT")
print("===================================")

print(
    f"Total companies: "
    f"{len(final_df)}"
)

print(
    f"Industry found: "
    f"{industry_found}"
)

print(
    f"Industry missing: "
    f"{industry_missing}"
)

print(
    "Saved: fundamentals.csv"
)

print("===================================")
print()


print(
    final_df[
        [
            "Company",
            "Symbol",
            "Industry"
        ]
    ].head(30).to_string(
        index=False
    )
)

