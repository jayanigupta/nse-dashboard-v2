import requests
import pandas as pd
from io import StringIO

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "*/*",
    "Referer": "https://www.nseindia.com/"
}

# Official NSE constituent CSVs
INDEX_URLS = {
    "Nifty 50":
        "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv",

    "Nifty 100":
        "https://nsearchives.nseindia.com/content/indices/ind_nifty100list.csv",

    "Nifty Total Market":
        "https://nsearchives.nseindia.com/content/indices/ind_niftytotalmarketlist.csv",

    "Nifty Midcap 150":
        "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap150list.csv",

    "Nifty Midcap 100":
        "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap100list.csv",

    "Nifty Smallcap 250":
        "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",

    "Nifty Smallcap 500":
        "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap500list.csv"
}


session = requests.Session()
session.headers.update(HEADERS)

# Open NSE first for cookies
session.get("https://www.nseindia.com/", timeout=20)

all_stocks = {}


for index_name, url in INDEX_URLS.items():

    print(f"Downloading {index_name}...")

    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()

        df = pd.read_csv(StringIO(response.text))

        # Find symbol column
        symbol_col = next(
            (col for col in df.columns
             if col.strip().lower() in ["symbol", "symbol "]),
            None
        )

        company_col = next(
            (col for col in df.columns
             if "company" in col.lower()),
            None
        )

        if symbol_col is None:
            print(f"ERROR: Could not find Symbol column for {index_name}")
            print(df.columns.tolist())
            continue

        for _, row in df.iterrows():

            symbol = str(row[symbol_col]).strip()

            if not symbol or symbol == "nan":
                continue

            company_name = ""

            if company_col:
                company_name = str(row[company_col]).strip()

            if symbol not in all_stocks:
                all_stocks[symbol] = {
                    "Symbol": symbol,
                    "Company Name": company_name
                }

            all_stocks[symbol][index_name] = "Yes"

        print(f"  Found {len(df)} stocks")

    except Exception as e:
        print(f"ERROR downloading {index_name}: {e}")


# Stop if nothing downloaded
if not all_stocks:
    raise RuntimeError(
        "No index data was downloaded. "
        "Check the NSE URLs or connection."
    )


# Create dataframe
result = pd.DataFrame(all_stocks.values())


# Add missing index columns
for index_name in INDEX_URLS:
    if index_name not in result.columns:
        result[index_name] = "No"


# Replace missing values
for index_name in INDEX_URLS:
    result[index_name] = result[index_name].fillna("No")


# Sort
result = result.sort_values("Symbol")


# Save
result.to_csv("nifty_indices.csv", index=False)


print()
print("======================================")
print("Created nifty_indices.csv")
print(f"Total unique stocks: {len(result)}")
print("======================================")
