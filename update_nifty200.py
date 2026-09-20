import pandas as pd
import requests
from io import StringIO

url = "https://nsearchives.nseindia.com/content/indices/ind_nifty200list.csv"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36",
    "Accept": "text/csv,text/plain,*/*",
    "Referer": "https://www.niftyindices.com/"
}

response = requests.get(url, headers=headers, timeout=30)
response.raise_for_status()

print("Downloaded:", len(response.content), "bytes")

df = pd.read_csv(StringIO(response.text))

print("Rows:", len(df))
print("Columns:", list(df.columns))

if len(df) == 0:
    raise ValueError("Nifty 200 data is empty!")

df.to_csv("nifty200.csv", index=False)

print("nifty200.csv created successfully!")
