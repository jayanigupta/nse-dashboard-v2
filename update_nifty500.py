import pandas as pd
import requests
from pathlib import Path
from datetime import date
from pandas.tseries.offsets import BDay

# -----------------------------------
# SETTINGS
# -----------------------------------

URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
OUTPUT_FILE = Path(__file__).resolve().parent / "nifty500.csv"


# -----------------------------------
# CHECK IF IT IS UPDATE TIME
# -----------------------------------

today = pd.Timestamp(date.today())

# First working day of April
first_april = pd.Timestamp(year=today.year, month=4, day=1)
first_april = first_april + BDay(0)

# First working day of October
first_october = pd.Timestamp(year=today.year, month=10, day=1)
first_october = first_october + BDay(0)

update_dates = {
    first_april.date(),
    first_october.date()
}

if today.date() not in update_dates:
    print("Not NIFTY 500 update day.")
    print(f"Today: {today.date()}")
    print("No changes made.")
    exit()


# -----------------------------------
# DOWNLOAD CURRENT NIFTY 500 LIST
# -----------------------------------

print("Updating NIFTY 500 list...")

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/csv,application/csv,text/plain,*/*",
    "Referer": "https://www.niftyindices.com/"
}

response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()


# -----------------------------------
# SAVE THE NEW CSV
# -----------------------------------

new_data = pd.read_csv(
    pd.io.common.BytesIO(response.content)
)

# Clean column names
new_data.columns = new_data.columns.str.strip()

# Make sure this is actually the expected NIFTY 500 file
required_columns = [
    "Company Name",
    "Industry",
    "Symbol",
    "Series",
    "ISIN Code"
]

missing = [col for col in required_columns if col not in new_data.columns]

if missing:
    raise ValueError(
        f"Downloaded file does not have expected columns. Missing: {missing}"
    )

# Save exactly where your dashboard expects it
new_data.to_csv(OUTPUT_FILE, index=False)

print("NIFTY 500 updated successfully.")
print(f"Stocks: {len(new_data)}")
print(f"File: {OUTPUT_FILE}")