import datetime
from pathlib import Path
import requests
import time

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.nseindia.com/",
}

today = datetime.date.today()

for i in range(45):
    date = today - datetime.timedelta(days=i)

    filename = f"sec_bhavdata_full_{date.strftime('%d%m%Y')}.csv"
    file_path = DATA_DIR / filename

    # ✅ SKIP if already exists
    if file_path.exists():
        continue

    url = f"https://nsearchives.nseindia.com/products/content/{filename}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=30)

        if r.status_code == 200 and len(r.content) > 1000:
            file_path.write_bytes(r.content)
            print("Downloaded:", filename)

        time.sleep(1)

    except Exception as e:
        print("Skipped:", filename, e)

import subprocess
import sys

subprocess.run([sys.executable, "build_avg_volume.py"])