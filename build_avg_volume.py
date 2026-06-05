import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")

# get all daily bhavcopy files
files = sorted(DATA_DIR.glob("sec_bhavdata_full_*.csv"))

all_dfs = []

for file in files:
    try:
        df = pd.read_csv(file)
        df.columns = df.columns.str.strip()

        # keep only required column
        if "SYMBOL" in df.columns and "TTL_TRD_QNTY" in df.columns:

            df["TTL_TRD_QNTY"] = pd.to_numeric(df["TTL_TRD_QNTY"], errors="coerce")

            all_dfs.append(df[["SYMBOL", "TTL_TRD_QNTY"]])

        print(f"Processed: {file.name}")

    except Exception as e:
        print(f"Skipped: {file.name} -> {e}")

# combine all days into one dataset
if all_dfs:
    history = pd.concat(all_dfs, ignore_index=True)
else:
    history = pd.DataFrame(columns=["SYMBOL", "TTL_TRD_QNTY"])

# compute average volume across ALL files in folder
avg_volume = (
    history.groupby("SYMBOL")["TTL_TRD_QNTY"]
    .mean()
    .reset_index()
    .rename(columns={"TTL_TRD_QNTY": "AVG_30D_VOLUME"})
)

# overwrite old file
avg_volume.to_csv("avg_volume.csv", index=False)

print("✅ avg_volume.csv updated successfully")
print("Stocks processed:", len(avg_volume))