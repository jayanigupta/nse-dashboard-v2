import requests
import pandas as pd
from io import StringIO

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/153.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": "https://www.niftyindices.com/"
}

# Official NSE/Nifty Indices constituent files
URLS = {
    "Nifty 50":
        "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv",

    "Nifty 100":
        "https://nsearchives.nseindia.com/content/indices/ind_nifty100list.csv",

    "Nifty Midcap 150":
        "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap150list.csv",

    "Nifty Midcap 100":
        "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap100list.csv",

    "Nifty Smallcap 250":
        "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",

    "Nifty Smallcap 500":
        "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap500list.csv",

    "Nifty Microcap 250":
        "https://nsearchives.nseindia.com/content/indices/ind_niftymicrocap250list.csv",
}


session = requests.Session()
session.headers.update(HEADERS)

# Open NSE first
session.get("https://www.nseindia.com/", timeout=30)


def download_index(index_name, url):

    print(f"Downloading {index_name}...")

    response = session.get(url, timeout=30)
    response.raise_for_status()

    df = pd.read_csv(StringIO(response.text))

    print(f"  Columns: {df.columns.tolist()}")
    print(f"  Rows: {len(df)}")

    # Find symbol column
    symbol_col = None

    for col in df.columns:
        if col.strip().upper() == "SYMBOL":
            symbol_col = col
            break

    if symbol_col is None:
        raise ValueError(
            f"Could not find SYMBOL column in {index_name}"
        )

    # Find company name column
    company_col = None

    for col in df.columns:
        if "company" in col.lower():
            company_col = col
            break

    output = pd.DataFrame()

    output["Symbol"] = (
        df[symbol_col]
        .astype(str)
        .str.strip()
    )

    if company_col:
        output["Company Name"] = (
            df[company_col]
            .astype(str)
            .str.strip()
        )
    else:
        output["Company Name"] = ""

    # Remove invalid rows
    output = output[
        (output["Symbol"] != "") &
        (output["Symbol"].str.lower() != "nan")
    ]

    return output


# ---------------------------------------------------------
# Download all indexes
# ---------------------------------------------------------

index_data = {}

for index_name, url in URLS.items():

    try:
        index_data[index_name] = download_index(
            index_name,
            url
        )

    except Exception as e:

        print(
            f"ERROR downloading {index_name}: {e}"
        )


# ---------------------------------------------------------
# Make sure required indexes downloaded
# ---------------------------------------------------------

required = [
    "Nifty 50",
    "Nifty 100",
    "Nifty Midcap 150",
    "Nifty Midcap 100",
    "Nifty Smallcap 250",
    "Nifty Smallcap 500",
    "Nifty Microcap 250",
]

missing = [
    name for name in required
    if name not in index_data
]

if missing:

    raise RuntimeError(
        "These indexes failed to download: "
        + ", ".join(missing)
    )


# ---------------------------------------------------------
# Create master stock list
# ---------------------------------------------------------

all_stocks = {}

for index_name, data in index_data.items():

    for _, row in data.iterrows():

        symbol = row["Symbol"]
        company = row["Company Name"]

        if symbol not in all_stocks:

            all_stocks[symbol] = {
                "Symbol": symbol,
                "Company Name": company
            }

        all_stocks[symbol][index_name] = "Yes"


# ---------------------------------------------------------
# Nifty Total Market
#
# Official definition:
# Nifty 500 + Nifty Microcap 250
# ---------------------------------------------------------

nifty500_url = (
    "https://nsearchives.nseindia.com/content/indices/"
    "ind_nifty500list.csv"
)

nifty500 = download_index(
    "Nifty 500",
    nifty500_url
)

nifty_total_symbols = set(
    nifty500["Symbol"]
).union(
    set(index_data["Nifty Microcap 250"]["Symbol"])
)


for symbol in nifty_total_symbols:

    if symbol not in all_stocks:

        # Find company name from Microcap 250
        company = ""

        micro = index_data["Nifty Microcap 250"]

        match = micro[
            micro["Symbol"] == symbol
        ]

        if not match.empty:
            company = match.iloc[0]["Company Name"]

        all_stocks[symbol] = {
            "Symbol": symbol,
            "Company Name": company
        }

    all_stocks[symbol]["Nifty Total Market"] = "Yes"


# ---------------------------------------------------------
# Create final dataframe
# ---------------------------------------------------------

result = pd.DataFrame(
    all_stocks.values()
)


# ---------------------------------------------------------
# Add every required column
# ---------------------------------------------------------

columns = [
    "Nifty 50",
    "Nifty 100",
    "Nifty Midcap 150",
    "Nifty Midcap 100",
    "Nifty Smallcap 250",
    "Nifty Total Market",
    "Nifty Smallcap 500"
]

for column in columns:

    if column not in result.columns:
        result[column] = "No"

    result[column] = (
        result[column]
        .fillna("No")
    )


# ---------------------------------------------------------
# Sort
# ---------------------------------------------------------

result = result.sort_values(
    "Symbol"
).reset_index(drop=True)


# ---------------------------------------------------------
# Keep only what the dashboard needs
# ---------------------------------------------------------

result = result[
    [
        "Symbol",
        "Company Name",
        "Nifty 50",
        "Nifty 100",
        "Nifty Midcap 150",
        "Nifty Midcap 100",
        "Nifty Smallcap 250",
        "Nifty Total Market",
        "Nifty Smallcap 500"
    ]
]


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

result.to_csv(
    "nifty_indices.csv",
    index=False
)


# ---------------------------------------------------------
# Verification
# ---------------------------------------------------------

print()
print("========================================")
print("Created nifty_indices.csv")
print("========================================")

print(
    f"Total stocks: {len(result)}"
)

for column in columns:

    count = (
        result[column]
        .eq("Yes")
        .sum()
    )

    print(
        f"{column}: {count}"
    )

print("========================================")
