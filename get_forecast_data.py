import time

import pandas as pd
import yfinance as yf


# ============================================================
# SETTINGS
# ============================================================

INPUT_FILE = "fundamentals.csv"
OUTPUT_FILE = "forecast.csv"

# Small delay to reduce the chance of Yahoo rate limiting us
DELAY_SECONDS = 0.5


# ============================================================
# LOAD THE EXISTING 500-COMPANY UNIVERSE
# ============================================================

fundamentals = pd.read_csv(INPUT_FILE)

symbols = (
    fundamentals["Symbol"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
)

print()
print(f"Companies to process: {len(symbols)}")
print()


# ============================================================
# FETCH FORECAST DATA
# ============================================================

results = []

for number, symbol in enumerate(symbols, start=1):

    yahoo_symbol = f"{symbol}.NS"

    print(
        f"[{number}/{len(symbols)}] "
        f"Fetching {symbol}..."
    )

    forecast_eps = None
    forecast_eps_growth = None
    forecast_revenue = None
    forecast_revenue_growth = None
    forward_pe = None
    analyst_count_eps = None
    analyst_count_revenue = None

    try:

        ticker = yf.Ticker(yahoo_symbol)

        # ----------------------------------------------------
        # Earnings estimates
        # ----------------------------------------------------

        earnings = ticker.get_earnings_estimate()

        if (
            earnings is not None
            and "+1y" in earnings.index
        ):

            forecast_eps = earnings.loc[
                "+1y",
                "avg"
            ]

            forecast_eps_growth = earnings.loc[
                "+1y",
                "growth"
            ]

            analyst_count_eps = earnings.loc[
                "+1y",
                "numberOfAnalysts"
            ]

        # ----------------------------------------------------
        # Revenue estimates
        # ----------------------------------------------------

        revenue = ticker.get_revenue_estimate()

        if (
            revenue is not None
            and "+1y" in revenue.index
        ):

            forecast_revenue = revenue.loc[
                "+1y",
                "avg"
            ]

            forecast_revenue_growth = revenue.loc[
                "+1y",
                "growth"
            ]

            analyst_count_revenue = revenue.loc[
                "+1y",
                "numberOfAnalysts"
            ]

        # ----------------------------------------------------
        # Current price
        #
        # Use the existing fundamentals.csv price.
        # This avoids another Yahoo request.
        # ----------------------------------------------------

        matching_rows = fundamentals[
            fundamentals["Symbol"].astype(str).str.strip()
            == symbol
        ]

        if not matching_rows.empty:

            current_price = pd.to_numeric(
                matching_rows.iloc[0]["CMP Rs."],
                errors="coerce"
            )

        else:

            current_price = None

        # ----------------------------------------------------
        # Forward P/E
        # ----------------------------------------------------

        if (
            pd.notna(current_price)
            and forecast_eps is not None
            and pd.notna(forecast_eps)
            and forecast_eps > 0
        ):

            forward_pe = (
                current_price / forecast_eps
            )

    except Exception as e:

        print(
            f"  Error for {symbol}: {e}"
        )

    results.append(
        {
            "Symbol": symbol,
            "Forecast EPS": forecast_eps,
            "Forecast EPS Growth": forecast_eps_growth,
            "Forward P/E": forward_pe,
            "Forecast Revenue": forecast_revenue,
            "Forecast Revenue Growth": forecast_revenue_growth,
            "EPS Analysts": analyst_count_eps,
            "Revenue Analysts": analyst_count_revenue,
        }
    )

    time.sleep(DELAY_SECONDS)


# ============================================================
# SAVE
# ============================================================

forecast = pd.DataFrame(results)

forecast.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print("=" * 60)
print("FORECAST DATA COMPLETE")
print("=" * 60)

print(
    f"Companies processed: {len(forecast)}"
)

print(
    f"Companies with Forecast EPS: "
    f"{forecast['Forecast EPS'].notna().sum()}"
)

print(
    f"Companies with Forward P/E: "
    f"{forecast['Forward P/E'].notna().sum()}"
)

print(
    f"Companies with Forecast Revenue: "
    f"{forecast['Forecast Revenue'].notna().sum()}"
)

print()
print(
    f"Saved to: {OUTPUT_FILE}"
)