import datetime
from pathlib import Path

import requests

DATA_DIR = Path('.')
OUTPUT_FILE = DATA_DIR / 'sec_bhavdata_latest.csv'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    'Referer': 'https://www.nseindia.com/',
}
NSE_BASE_URL = 'https://nsearchives.nseindia.com/products/content'
MAX_LOOKBACK_DAYS = 7


def build_bhavcopy_url(date: datetime.date) -> str:
    return f"{NSE_BASE_URL}/sec_bhavdata_full_{date.strftime('%d%m%Y')}.csv"


def get_candidate_dates() -> list[datetime.date]:
    today = datetime.date.today()
    return [today - datetime.timedelta(days=i) for i in range(MAX_LOOKBACK_DAYS)]


def download_bhavcopy(date: datetime.date) -> bytes:
    url = build_bhavcopy_url(date)
    response = requests.get(url, headers=HEADERS, timeout=60)
    response.raise_for_status()
    if len(response.content) < 200:
        raise ValueError(f"Received too little data for {date}")
    return response.content


def main() -> None:
    print('Searching for the latest available bhavcopy...')

    for candidate_date in get_candidate_dates():
        try:
            content = download_bhavcopy(candidate_date)
            OUTPUT_FILE.write_bytes(content)
            print(f'Saved latest bhavcopy to {OUTPUT_FILE} for date {candidate_date:%Y-%m-%d}')
            return
        except Exception as exc:
            print(f'  skipped {candidate_date:%Y-%m-%d}: {exc}')

    raise RuntimeError('Could not download any bhavcopy file from NSE archives.')


if __name__ == '__main__':
    main()