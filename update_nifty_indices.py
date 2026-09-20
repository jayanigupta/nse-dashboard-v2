import requests
import pandas as pd
import time

URL = "https://www.nseindia.com/api/equity-stockIndices"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/153.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/"
}

# These are the indexes we want in the NEW file.
# Nifty 200 and Nifty 500 are deliberately NOT included.
INDEXES = {
    "Nifty 50": "NIFTY 50",
    "Nifty 100": "NIFTY 100",
    "Nifty Total Market": "NIFTY TOTAL MARKET",
    "Nifty Midcap 150": "NIFTY MIDCAP 150",
    "Nifty Midcap 100": "NIFTY MIDCAP 100",
    "Nifty Smallcap 250": "NIFTY SMALLCAP 250",
    "Nifty Smallcap 500": "NIFTY SMALLCAP 500"
}

session = requests.Session()
session.headers.update(HEADERS)

# Open NSE first so the API request gets the required cookies
session.get("https://www.nseindia.com/", timeout=20)

all_stocks = {}

for index_name, nse_index_name in INDEXES.items():

    print(f"Downloading {index_name}...")

    try:
        response = session.get(
            URL,
            params={"index": nse_index_name},
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        stocks = data.get("data", [])

        if not stocks:
            print(f"WARNING: No stocks found for {index_name}")
            continue

        for stock in stocks:

            symbol = stock.get("symbol")

            # Ignore the index itself if NSE returns it
            if not symbol or symbol == nse_index_name:
                continue

            if symbol not in all_stocks:
                all_stocks[symbol] = {
                    "Symbol": symbol,
                    "Company Name": stock.get("meta", {}).get(
                        "companyName", ""
                    )
                }

            all_stocks[symbol][index_name] = "Yes"

        print(f"  Found {len(stocks)} stocks")

        time.sleep(1)

    except Exception as e:
        print(f"ERROR downloading {index_name}: {e}")


# Convert to DataFrame
df = pd.DataFrame(all_stocks.values())

# Make sure every index column exists
for index_name in INDEXES:
    if index_name not in df.columns:
        df[index_name] = "No"

# Fill missing memberships
for index_name in INDEXES:
    df[index_name] = df[index_name].fillna("No")

# Sort alphabetically by symbol
df = df.sort_values("Symbol")

# Save the NEW file
df.to_csv("nifty_indices.csv", index=False)

print()
print("====================================")
print("Created nifty_indices.csv")
print(f"Total unique stocks: {len(df)}")
print("====================================")
print()
print(df.head())
