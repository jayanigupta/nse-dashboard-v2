import pandas as pd
import requests
from io import BytesIO

url = "https://nsearchives.nseindia.com/content/indices/ind_nifty200list.csv"

headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.niftyindices.com/"
}

response = requests.get(url, headers=headers, timeout=30)
response.raise_for_status()

df = pd.read_csv(BytesIO(response.content))

df.to_csv("nifty200.csv", index=False)

print(f"Nifty 200 updated: {len(df)} stocks")
