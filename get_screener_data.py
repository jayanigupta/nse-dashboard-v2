import os
import re
import shutil
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import StringIO


# ============================================================
# SETTINGS
# ============================================================

FUNDAMENTALS_FILE = "fundamentals.csv"
MARKETLENS_FILE = "marketlens.csv"

BACKUP_FILE = "fundamentals.csv.backup"
TEMP_FILE = "fundamentals.csv.tmp"

BASE_URL = (
    "https://www.screener.in/screens/"
    "508045/price-to-book-ratio/"
)

SCREENER_PAGES = 19
REQUEST_DELAY = 2


# ============================================================
# REQUIRED FUNDAMENTALS COLUMNS
# ============================================================

REQUIRED_COLUMNS = [
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
    "ROE 10Yr %",
    "CMP / BV",
    "Ind PBV",
    "Symbol",
    "Industry",
]


# ============================================================
# INDUSTRY NORMALIZATION
#
# ONLY used for the existing Industry column and peer PBV.
#
# Market Lens Sector/Sub Sector NEVER replaces Industry.
# ============================================================

industry_normalization = {

    "Capital Markets": "Financial Services",
    "Financial Data & Stock Exchanges": "Financial Services",
    "Financial Services - Misc": "Financial Services",

    "Information Technology Services":
        "Information Technology",

    "Specialty Chemicals": "Chemicals",
    "Commodity Chemicals": "Chemicals",

    "Auto Parts":
        "Automobiles & Auto Components",

    "Automobile and Auto Components":
        "Automobiles & Auto Components",

    "Industrial Machinery":
        "Capital Goods & Machinery",

    "Specialty Industrial Machinery":
        "Capital Goods & Machinery",

    "Farm & Heavy Construction Machinery":
        "Capital Goods & Machinery",

    "Engineering - Industrial Equipments":
        "Capital Goods & Machinery",

    "Apparel Manufacturing":
        "Textiles & Apparel",

    "Realty":
        "Real Estate",

    "Real Estate - Development":
        "Real Estate",

    "Real Estate Services":
        "Real Estate",

    "Telecommunication":
        "Telecommunications",

    "Telecom Services":
        "Telecommunications",

    "Telecommunications - Equipment":
        "Telecommunications",

    "Other Industrial Metals & Mining":
        "Metals & Mining",

    "Aluminum":
        "Metals & Mining",

    "Electronics & Components":
        "Electrical & Electronics",

    "Electronics - Components":
        "Electrical & Electronics",

    "Electrical Equipment & Parts":
        "Electrical & Electronics",

    "Communication Equipment":
        "Telecommunications",

    "Retail - Speciality":
        "Retail",

    "Specialty Retail":
        "Retail",

    "Apparel Retail":
        "Retail",

    "Pharmaceutical Retailers":
        "Retail",

    "Media Entertainment & Publication":
        "Media & Entertainment",

    "Publishing":
        "Media & Entertainment",

    "Integrated Freight & Logistics":
        "Transportation & Logistics",

    "Trucking":
        "Transportation & Logistics",

    "Airports & Air Services":
        "Transportation & Logistics",

    "Lodging":
        "Hotels & Resorts",

    "Resorts & Casinos":
        "Hotels & Resorts",

    "Oil Gas & Consumable Fuels":
        "Oil & Gas",

    "Oil & Gas Refining & Marketing":
        "Oil & Gas",

    "Oil & Gas Equipment & Services":
        "Oil & Gas",

    "Packaged Foods":
        "Food & Beverages",

    "Confectioners":
        "Food & Beverages",

    "Food Distribution":
        "Food & Beverages",

    "Beverages - Wineries & Distilleries":
        "Beverages & Tobacco",

    "Tobacco":
        "Beverages & Tobacco",

    "Engineering & Construction":
        "Construction & Building",

    "Construction":
        "Construction & Building",

    "Building Products & Equipment":
        "Construction & Building",

    "Construction Materials":
        "Construction & Building",

    "Diversified - Medium / Small":
        "Diversified",

    "Conglomerates":
        "Diversified",

    "Specialty Business Services":
        "Business Services",

    "Business Equipment & Supplies":
        "Business Services",

    "Paper & Paper Products":
        "Paper & Forest Products",

    "Lumber & Wood Production":
        "Paper & Forest Products",
}


# ============================================================
# HELPERS
# ============================================================

def clean_number(value):
    """
    Convert common financial strings to numbers.
    """

    if pd.isna(value):
        return None

    value = str(value).strip()

    if value in {
        "",
        "-",
        "--",
        "NA",
        "N/A",
        "nan",
        "None",
    }:
        return None

    value = value.replace(",", "")
    value = value.replace("%", "")

    try:
        return float(value)
    except Exception:
        return None


def normalize_symbol(symbol):

    if pd.isna(symbol):
        return ""

    return str(symbol).strip().upper()


# ============================================================
# START
# ============================================================

print()
print("=" * 50)
print("SAFE DAILY FUNDAMENTALS UPDATE")
print("=" * 50)
print()


# ============================================================
# LOAD EXISTING FUNDAMENTALS
# ============================================================

if not os.path.exists(FUNDAMENTALS_FILE):

    raise FileNotFoundError(
        f"{FUNDAMENTALS_FILE} was not found."
    )


current = pd.read_csv(
    FUNDAMENTALS_FILE
)


# ============================================================
# VERIFY REQUIRED COLUMNS
# ============================================================

missing_columns = [
    column
    for column in REQUIRED_COLUMNS
    if column not in current.columns
]

if missing_columns:

    raise RuntimeError(
        "fundamentals.csv is missing columns: "
        f"{missing_columns}"
    )


# ============================================================
# VERIFY 500-COMPANY MASTER UNIVERSE
# ============================================================

current["Symbol"] = (
    current["Symbol"]
    .map(normalize_symbol)
)

ORIGINAL_ROWS = len(current)

ORIGINAL_SYMBOLS = set(
    current["Symbol"]
)

print(
    f"Existing companies: "
    f"{ORIGINAL_ROWS}"
)


if ORIGINAL_ROWS != 500:

    raise RuntimeError(
        "SAFETY STOP: expected exactly "
        f"500 companies, found {ORIGINAL_ROWS}."
    )


if current["Symbol"].duplicated().any():

    duplicates = (
        current.loc[
            current["Symbol"].duplicated(),
            "Symbol"
        ]
        .tolist()
    )

    raise RuntimeError(
        "SAFETY STOP: duplicate symbols found: "
        f"{duplicates}"
    )


# ============================================================
# LOAD MARKET LENS
# ============================================================

marketlens = None

if os.path.exists(MARKETLENS_FILE):

    print()
    print("Loading Market Lens...")

    marketlens = pd.read_csv(
        MARKETLENS_FILE
    )

    required_ml = [
        "Company",
        "Market Cap",
        "PE Ratio",
        "Dividend Yield (%)",
    ]

    missing_ml = [
        column
        for column in required_ml
        if column not in marketlens.columns
    ]

    if missing_ml:

        raise RuntimeError(
            "Market Lens file is missing columns: "
            f"{missing_ml}"
        )

    print(
        f"Market Lens rows: "
        f"{len(marketlens)}"
    )


    # --------------------------------------------------------
    # Extract symbol from:
    #
    # Reliance Industries Limited (RELIANCE)
    # --------------------------------------------------------

    marketlens["Symbol"] = (
        marketlens["Company"]
        .astype(str)
        .str.extract(
            r"\(([^()]+)\)\s*$"
        )[0]
        .map(normalize_symbol)
    )


    marketlens = marketlens[
        marketlens["Symbol"] != ""
    ].copy()


    # --------------------------------------------------------
    # Prevent duplicate symbols
    # --------------------------------------------------------

    duplicate_ml = marketlens[
        marketlens["Symbol"]
        .duplicated(keep=False)
    ]

    if len(duplicate_ml):

        print(
            "WARNING: "
            f"{duplicate_ml['Symbol'].nunique()} "
            "duplicate Market Lens symbols found."
        )

        marketlens = (
            marketlens
            .drop_duplicates(
                subset=["Symbol"],
                keep="first"
            )
        )


else:

    print()
    print(
        "WARNING: marketlens.csv not found."
    )

    print(
        "Market Lens update will be skipped."
    )


# ============================================================
# APPLY MARKET LENS
#
# Market Lens ONLY updates:
#
#   Market Cap
#   P/E
#   Dividend Yield
#
# It NEVER changes:
#
#   Company
#   Symbol
#   Industry
# ============================================================

marketlens_updated_cells = 0
marketlens_matched = 0

if marketlens is not None:

    ml_lookup = (
        marketlens
        .set_index("Symbol")
    )

    for idx in current.index:

        symbol = current.at[
            idx,
            "Symbol"
        ]

        if symbol not in ml_lookup.index:
            continue

        marketlens_matched += 1

        row = ml_lookup.loc[
            symbol
        ]


        # ----------------------------------------------------
        # MARKET CAP
        # ----------------------------------------------------

        market_cap = clean_number(
            row["Market Cap"]
        )

        if market_cap is not None:

            market_cap_crore = (
                market_cap / 10_000_000
            )

            current.at[
                idx,
                "Mar Cap Rs.Cr."
            ] = market_cap_crore

            marketlens_updated_cells += 1


        # ----------------------------------------------------
        # P/E
        # ----------------------------------------------------

        pe = clean_number(
            row["PE Ratio"]
        )

        if pe is not None:

            current.at[
                idx,
                "P/E"
            ] = pe

            marketlens_updated_cells += 1


        # ----------------------------------------------------
        # DIVIDEND YIELD
        # ----------------------------------------------------

        div_yield = clean_number(
            row["Dividend Yield (%)"]
        )

        if div_yield is not None:

            current.at[
                idx,
                "Div Yld %"
            ] = div_yield

            marketlens_updated_cells += 1


print()
print("Market Lens:")
print(
    f"Matched companies: "
    f"{marketlens_matched}"
)
print(
    f"Cells updated: "
    f"{marketlens_updated_cells}"
)


# ============================================================
# SCREENER SESSION
# ============================================================

session = requests.Session()

session.headers.update({

    "User-Agent": (
        "Mozilla/5.0 "
        "(Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/153.0 Safari/537.36"
    )

})


# ============================================================
# SCRAPE SCREENER
#
# THIS USES THE METHOD FROM YOUR OLD WORKING CODE:
#
# 1. ?page=1
# 2. ?page=2
# 3. ...
# 4. data-row-company-id
# 5. pd.read_html()
# ============================================================

print()
print("=" * 50)
print("Fetching Screener pages")
print("=" * 50)
print()


all_screener_data = []


for page in range(
    1,
    SCREENER_PAGES + 1
):

    print(
        f"Fetching page "
        f"{page}/{SCREENER_PAGES}..."
    )


    # --------------------------------------------------------
    # SAME PAGINATION AS YOUR OLD CODE
    # --------------------------------------------------------

    url = (
        f"{BASE_URL}?page={page}"
    )


    response = requests.get(
        url,
        headers=session.headers,
        timeout=30
    )

    response.raise_for_status()


    # --------------------------------------------------------
    # PARSE HTML
    # --------------------------------------------------------

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )


    # --------------------------------------------------------
    # EXTRACT SYMBOLS
    #
    # Same method as your old code.
    # --------------------------------------------------------

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
                    parts.index(
                        "company"
                    )
                )


                symbol = (
                    parts[
                        company_index + 1
                    ]
                )


                symbols.append(
                    normalize_symbol(
                        symbol
                    )
                )


            except (
                ValueError,
                IndexError
            ):

                symbols.append(None)


        else:

            symbols.append(None)


    # --------------------------------------------------------
    # EXTRACT TABLE
    #
    # Same pd.read_html approach as old code.
    # --------------------------------------------------------

    tables = pd.read_html(
        StringIO(
            response.text
        )
    )


    if not tables:

        raise RuntimeError(
            "SAFETY STOP: "
            f"No table found on Screener "
            f"page {page}."
        )


    df = tables[0].copy()


    # --------------------------------------------------------
    # REMOVE REPEATED HEADER ROWS
    # --------------------------------------------------------

    if "S.No." in df.columns:

        df = df[
            df["S.No."]
            .astype(str)
            != "S.No."
        ].copy()


    # --------------------------------------------------------
    # ADD SYMBOL
    # --------------------------------------------------------

    if len(symbols) == len(df):

        df["Symbol"] = symbols


    else:

        print()
        print(
            "WARNING page "
            f"{page}: "
            f"{len(df)} table rows vs "
            f"{len(symbols)} symbols"
        )

        # Do NOT try to guess alignment.
        # This protects the data.

        df["Symbol"] = None


    # --------------------------------------------------------
    # KEEP DATA
    # --------------------------------------------------------

    all_screener_data.append(
        df
    )


    print(
        f"  → {len(df)} companies"
    )


    time.sleep(
        REQUEST_DELAY
    )


# ============================================================
# COMBINE SCREENER DATA
# ============================================================

if not all_screener_data:

    raise RuntimeError(
        "SAFETY STOP: "
        "Screener returned no data."
    )


screener = pd.concat(
    all_screener_data,
    ignore_index=True
)


screener["Symbol"] = (
    screener["Symbol"]
    .map(normalize_symbol)
)


print()
print(
    f"Total Screener rows: "
    f"{len(screener)}"
)


# ============================================================
# NORMALIZE SCREENER COLUMNS
# ============================================================

def get_value(
    row,
    possible_columns
):

    for column in possible_columns:

        if column in row.index:

            value = row[column]

            if (
                pd.notna(value)
                and
                str(value).strip() != ""
            ):

                return value

    return None


def normalize_screen_row(row):
    return {

        "CMP Rs.": get_value(
            row,
            [
                "CMP  Rs.",
                "CMP",
                "Current Price"
            ]
        ),

        "NP Qtr Rs.Cr.": get_value(
            row,
            [
                "NP Qtr  Rs.Cr.",
                "NP Qtr",
                "Net Profit"
            ]
        ),

        "Qtr Profit Var %": get_value(
            row,
            [
                "Qtr Profit Var  %",
                "Qtr Profit Var",
                "Profit Var"
            ]
        ),

        "Sales Qtr Rs.Cr.": get_value(
            row,
            [
                "Sales Qtr  Rs.Cr.",
                "Sales Qtr",
                "Sales"
            ]
        ),

        "Qtr Sales Var %": get_value(
            row,
            [
                "Qtr Sales Var  %",
                "Qtr Sales Var",
                "Sales Var"
            ]
        ),

        "ROCE %": get_value(
            row,
            [
                "ROCE  %",
                "ROCE"
            ]
        ),

        "ROE 10Yr %": get_value(
            row,
            [
                "ROE 10Yr  %",
                "ROE 10Yr",
                "ROE"
            ]
        ),

        "CMP / BV": get_value(
            row,
            [
                "CMP / BV",
                "Price to book value",
                "P/B"
            ]
        ),

    }

def fetch_missing_pb_from_screener(symbol):

    if not symbol:
        return None

    url = f"https://www.screener.in/company/{symbol}/"

    try:

        response = requests.get(
            url,
            headers=session.headers,
            timeout=20
        )

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        top_ratios = soup.select_one(
            "#top-ratios"
        )

        if not top_ratios:
            return None

        text = top_ratios.get_text(
            " ",
            strip=True
        )

        price_match = re.search(
            r"Current Price\s*₹?\s*([\d,]+(?:\.\d+)?)",
            text
        )

        book_match = re.search(
            r"Book Value\s*₹?\s*([\d,]+(?:\.\d+)?)",
            text
        )

        if not price_match or not book_match:
            return None

        current_price = float(
            price_match.group(1).replace(",", "")
        )

        book_value = float(
            book_match.group(1).replace(",", "")
        )

        if book_value == 0:
            return None

        pb = current_price / book_value
        return pb

    except Exception as e:

        print(
            f"P/B fetch error for {symbol}: {e}"
        )

        return None

        # ============================================================
        # SECOND FALLBACK
        #
        # Search the entire Screener page for Current Price + Book Value
        # ============================================================

        full_text = soup.get_text(
            " ",
            strip=True
        )

        price_match = re.search(
            r"Current Price\s*₹?\s*([\d,]+(?:\.\d+)?)",
            full_text
        )

        book_match = re.search(
            r"Book Value\s*₹?\s*([\d,]+(?:\.\d+)?)",
            full_text
        )

        if price_match and book_match:

            current_price = float(
                price_match.group(1).replace(",", "")
            )

            book_value = float(
                book_match.group(1).replace(",", "")
            )

            if book_value != 0:

                pb = current_price / book_value

                print(
                    f"P/B recovered using fallback: "
                    f"{symbol} -> {pb:.2f}"
                )

                return pb

# ============================================================
# APPLY SCREENER DATA
#
# Only existing 500 companies can be updated.
# ============================================================

screener_matches = 0
screener_cells_updated = 0

# Make financial columns able to accept Screener values
# before the final numeric conversion below.
for column in [
    "CMP Rs.",
    "P/E",
    "Mar Cap Rs.Cr.",
    "Div Yld %",
    "NP Qtr Rs.Cr.",
    "Qtr Profit Var %",
    "Sales Qtr Rs.Cr.",
    "Qtr Sales Var %",
    "ROCE %",
    "ROE 10Yr %",
    "CMP / BV",
]:
    current[column] = current[column].astype(object)


for _, row in screener.iterrows():

    symbol = normalize_symbol(
        row["Symbol"]
    )


    if symbol not in ORIGINAL_SYMBOLS:
        continue


    idx_list = current.index[
        current["Symbol"] == symbol
    ].tolist()


    if not idx_list:
        continue


    idx = idx_list[0]


    normalized = (
        normalize_screen_row(row)
    )


    for column, value in normalized.items():

        if value is None:
            continue


        current.at[
            idx,
            column
        ] = value


        screener_cells_updated += 1


    screener_matches += 1


print()
print("Screener:")
print(
    f"Matched companies: "
    f"{screener_matches}"
)
print(
    f"Cells updated: "
    f"{screener_cells_updated}"
)


# ============================================================
# RETRY MISSING P/B VALUES
#
# Only companies still missing CMP / BV are fetched
# individually from their Screener company page.
# ============================================================

missing_pb_mask = pd.to_numeric(
    current["CMP / BV"],
    errors="coerce"
).isna()

missing_pb = current[
    missing_pb_mask
].copy()

print()
print(
    f"Missing P/B values before retry: "
    f"{len(missing_pb)}"
)

pb_recovered = 0

for index, row in missing_pb.iterrows():

    symbol = normalize_symbol(
        row["Symbol"]
    )

    if not symbol:
        continue

    pb_value = fetch_missing_pb_from_screener(
        symbol
    )

    if pb_value is not None:

        current.at[
            index,
            "CMP / BV"
        ] = pb_value

        pb_recovered += 1

        print(
            f"P/B recovered: "
            f"{symbol} -> {pb_value}"
        )

    else:

        print(
            f"P/B still unavailable: "
            f"{symbol}"
        )

print()
print(
    f"P/B values recovered: "
    f"{pb_recovered}"
)



# ============================================================
# NORMALIZE NUMERIC FIELDS
# ============================================================

numeric_columns = [

    "CMP Rs.",
    "P/E",
    "Mar Cap Rs.Cr.",
    "Div Yld %",
    "NP Qtr Rs.Cr.",
    "Qtr Profit Var %",
    "Sales Qtr Rs.Cr.",
    "Qtr Sales Var %",
    "ROCE %",
    "ROE 10Yr %",
    "CMP / BV",
    "Ind PBV",

]


for column in numeric_columns:

    current[column] = pd.to_numeric(
        current[column],
        errors="coerce"
    )


# ============================================================
# INDUSTRY PBV
#
# Median CMP / BV within the same normalized Industry.
#
# This is a peer-group median, NOT an official NSE
# published industry PBV.
# ============================================================

current["Industry"] = (
    current["Industry"]
    .astype(str)
    .str.strip()
)


current["Industry"] = (
    current["Industry"]
    .replace(
        industry_normalization
    )
)


valid_pbv = current[
    current["CMP / BV"].notna()
    &
    (current["CMP / BV"] > 0)
    &
    current["Industry"].notna()
    &
    (current["Industry"] != "")
].copy()


industry_medians = (
    valid_pbv
    .groupby("Industry")["CMP / BV"]
    .median()
)


current["Ind PBV"] = (
    current["Industry"]
    .map(industry_medians)
)


# ============================================================
# FINAL SAFETY CHECKS
# ============================================================

print()
print("Running safety checks...")


# Row count

if len(current) != ORIGINAL_ROWS:

    raise RuntimeError(
        "SAFETY STOP: row count changed."
    )


# Exact universe

if (
    set(current["Symbol"])
    != ORIGINAL_SYMBOLS
):

    raise RuntimeError(
        "SAFETY STOP: "
        "company universe changed."
    )


# Duplicate symbols

if current["Symbol"].duplicated().any():

    raise RuntimeError(
        "SAFETY STOP: "
        "duplicate symbols after update."
    )


# Exactly 500 companies

if len(current) != 500:

    raise RuntimeError(
        "SAFETY STOP: "
        "final file is not 500 companies."
    )


# Required columns

for column in REQUIRED_COLUMNS:

    if column not in current.columns:

        raise RuntimeError(
            "SAFETY STOP: "
            f"missing final column {column}"
        )


# ============================================================
# PRESERVE COLUMN ORDER
# ============================================================

current = current[
    REQUIRED_COLUMNS
]


# ============================================================
# WRITE TEMP FILE
# ============================================================

current.to_csv(
    TEMP_FILE,
    index=False
)


print()
print(
    f"Temporary file written: "
    f"{TEMP_FILE}"
)


# ============================================================
# VALIDATE TEMP FILE
# ============================================================

test = pd.read_csv(
    TEMP_FILE
)


if len(test) != 500:

    os.remove(
        TEMP_FILE
    )

    raise RuntimeError(
        "SAFETY STOP: "
        "temporary file validation failed."
    )


if (
    test["Symbol"].nunique()
    != 500
):

    os.remove(
        TEMP_FILE
    )

    raise RuntimeError(
        "SAFETY STOP: "
        "duplicate symbols in "
        "temporary file."
    )


if (
    set(test["Symbol"])
    != ORIGINAL_SYMBOLS
):

    os.remove(
        TEMP_FILE
    )

    raise RuntimeError(
        "SAFETY STOP: "
        "temporary file changed universe."
    )


# ============================================================
# BACKUP CURRENT FILE
# ============================================================

shutil.copy2(
    FUNDAMENTALS_FILE,
    BACKUP_FILE
)


# ============================================================
# ATOMIC REPLACEMENT
# ============================================================

os.replace(
    TEMP_FILE,
    FUNDAMENTALS_FILE
)


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 50)
print("SAFE DAILY UPDATE COMPLETE")
print("=" * 50)

print(
    f"Companies preserved: "
    f"{len(current)}"
)

print(
    f"Screener matches: "
    f"{screener_matches}"
)

print(
    f"Market Lens matches: "
    f"{marketlens_matched}"
)

print(
    f"Market Lens cells updated: "
    f"{marketlens_updated_cells}"
)

print(
    f"Backup: "
    f"{BACKUP_FILE}"
)

print(
    f"Updated: "
    f"{FUNDAMENTALS_FILE}"
)

print(
    "Universe changed: NO"
)

print("=" * 50)