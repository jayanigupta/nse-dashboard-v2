import pandas as pd
import requests

BASE_URL = "https://www.screener.in/screens/508045/price-to-book-ratio/"

all_data = []

headers = {
    "User-Agent": "Mozilla/5.0"
}

for page in range(1, 20):

    print(f"Fetching page {page}/19...")

    url = f"{BASE_URL}?page={page}"

    response = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    tables = pd.read_html(response.text)

    if not tables:
        print(f"No table found on page {page}")
        continue

    df = tables[0]

    all_data.append(df)

    print(f"  → {len(df)} companies")

# Combine all pages
final_df = pd.concat(
    all_data,
    ignore_index=True
)

# Remove duplicate rows if any
final_df = final_df.drop_duplicates()

# Save
final_df.to_csv(
    "fundamentals.csv",
    index=False
)

print()
print("===================================")
print(f"Total companies: {len(final_df)}")
print("Saved: fundamentals.csv")
print("===================================")

print()
print(final_df.head())
