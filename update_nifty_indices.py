import requests
import pandas as pd

BASE_URL = "https://www.niftyindices.com/IndexConstituent/"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Referer": "https://www.niftyindices.com/"
}

# Official Nifty Indices constituent files
INDEX_FILES = {
    "Nifty 50": "ind_nifty50list.csv",
    "Nifty 100": "ind_nifty100list.csv",
    "Nifty Midcap 150": "ind_niftymidcap150list.csv",
    "Nifty Midcap 100": "ind_niftymidcap100list.csv",
    "Nifty Smallcap 250": "ind_niftysmallcap250list.csv",
    "Nifty Smallcap 500": "ind_NiftySmallcap500_list.csv",
    "Nifty Microcap 250": "ind_niftymicrocap250_list.csv",
}


def download_index(index_name, filename):
    url = BASE_URL + filename

    print(f"Downloading {index_name}...")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    df = pd.read_csv(
        pd.io.common.BytesIO(response.content)
    )

    # Clean column names
    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    print(f"  Found {len(df)} stocks")
    print(f"  Columns: {df.columns.tolist()}")

    # Find Symbol column
    symbol_col = next(
        (
            col for col in df.columns
            if col.upper() == "SYMBOL"
        ),
        None
    )

    # Find company name column
    company_col = next(
        (
            col for col in df.columns
            if "COMPANY" in col.upper()
        ),
        None
    )

    if symbol_col is None:
        raise ValueError(
            f"Could not find Symbol column for {index_name}"
        )

    result = pd.DataFrame()

    result["Symbol"] = (
        df[symbol_col]
        .astype(str)
        .str.strip()
    )

    if company_col:
        result["Company Name"] = (
            df[company_col]
            .astype(str)
            .str.strip()
        )
    else:
        result["Company Name"] = ""

    result = result[
        result["Symbol"].notna()
        & (result["Symbol"] != "")
        & (result["Symbol"].str.lower() != "nan")
    ]

    return result


# ============================================================
# Download the 7 indexes we need
# ============================================================

index_data = {}

for index_name, filename in INDEX_FILES.items():

    try:
        index_data[index_name] = download_index(
            index_name,
            filename
        )

    except Exception as e:
        print(
            f"ERROR downloading {index_name}: {e}"
        )
        raise


# ============================================================
# Build master list
# ============================================================

all_stocks = {}


for index_name, data in index_data.items():

    # Microcap is only needed to build Total Market
    if index_name == "Nifty Microcap 250":
        continue

    for _, row in data.iterrows():

        symbol = row["Symbol"]

        if symbol not in all_stocks:
            all_stocks[symbol] = {
                "Symbol": symbol,
                "Company Name": row["Company Name"]
            }

        all_stocks[symbol][index_name] = "Yes"


# ============================================================
# Nifty Total Market
#
# Official definition:
# Nifty 500 + Nifty Microcap 250
# ============================================================

print()
print("Building Nifty Total Market...")


# IMPORTANT:
# Use your existing nifty500.csv.
# We do NOT modify it.

nifty500 = pd.read_csv("nifty500.csv")

nifty500.columns = [
    str(col).strip()
    for col in nifty500.columns
]

nifty500_symbols = set(
    nifty500["Symbol"]
    .astype(str)
    .str.strip()
)


microcap = index_data["Nifty Microcap 250"]

microcap_symbols = set(
    microcap["Symbol"]
    .astype(str)
    .str.strip()
)

total_market_symbols = (
    nifty500_symbols
    | microcap_symbols
)


for symbol in total_market_symbols:

    if symbol not in all_stocks:

        # Try to get company name from Microcap
        match = microcap[
            microcap["Symbol"] == symbol
        ]

        if not match.empty:
            company_name = match.iloc[0]["Company Name"]
        else:
            company_name = ""

        all_stocks[symbol] = {
            "Symbol": symbol,
            "Company Name": company_name
        }

    all_stocks[symbol]["Nifty Total Market"] = "Yes"


# ============================================================
# Create final dataframe
# ============================================================

result = pd.DataFrame(
    all_stocks.values()
)


# ============================================================
# Make sure every requested index has a column
# ============================================================

FINAL_INDEXES = [
    "Nifty 50",
    "Nifty 100",
    "Nifty Total Market",
    "Nifty Midcap 150",
    "Nifty Midcap 100",
    "Nifty Smallcap 250",
    "Nifty Smallcap 500",
]


for index_name in FINAL_INDEXES:

    if index_name not in result.columns:
        result[index_name] = "No"

    result[index_name] = (
        result[index_name]
        .fillna("No")
    )


# ============================================================
# Sort
# ============================================================

result = result.sort_values(
    "Symbol"
).reset_index(drop=True)


# ============================================================
# Final column order
# ============================================================

result = result[
    [
        "Symbol",
        "Company Name",
        "Nifty 50",
        "Nifty 100",
        "Nifty Total Market",
        "Nifty Midcap 150",
        "Nifty Midcap 100",
        "Nifty Smallcap 250",
        "Nifty Smallcap 500",
    ]
]


# ============================================================
# Save
# ============================================================

result.to_csv(
    "nifty_indices.csv",
    index=False
)


# ============================================================
# Verification
# ============================================================

print()
print("========================================")
print("Created nifty_indices.csv")
print("========================================")

print(
    f"Total unique stocks: {len(result)}"
)

for index_name in FINAL_INDEXES:

    count = (
        result[index_name]
        .eq("Yes")
        .sum()
    )

    print(
        f"{index_name}: {count}"
    )

print("========================================")
