import requests

url = "https://nsearchives.nseindia.com/products/content/sec_bhavdata_full_02062026.csv"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer": "https://www.nseindia.com/",
}

print("Downloading...")

r = requests.get(
    url,
    headers=headers,
    timeout=60
)

print("Status:", r.status_code)
print("Size:", len(r.content))

with open("test.csv", "wb") as f:
    f.write(r.content)

print("Saved")