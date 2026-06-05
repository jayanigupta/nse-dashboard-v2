from pathlib import Path
import pandas as pd

DATA_DIR = Path("data")

all_files = sorted(
    DATA_DIR.glob("sec_bhavdata_full_*.csv")
)

periods = {
    "1d": 1,
    "1w": 7,
    "1m": 30,
    "3m": 90,
}

for label, days in periods.items():

    files = all_files[-days:]

    all_dfs = []

    for file in files:
        try:
            df = pd.read_csv(file)

            df.columns = df.columns.str.strip()

            if "SYMBOL" not in df.columns:
                continue

            if "TTL_TRD_QNTY" not in df.columns:
                continue

            df["TTL_TRD_QNTY"] = pd.to_numeric(
                df["TTL_TRD_QNTY"],
                errors="coerce"
            )

            all_dfs.append(
                df[["SYMBOL", "TTL_TRD_QNTY"]]
            )

        except Exception as e:
            print("Skipped:", file.name, e)

    if not all_dfs:
        continue

    history = pd.concat(
        all_dfs,
        ignore_index=True
    )

    avg_volume = (
        history
        .groupby("SYMBOL")["TTL_TRD_QNTY"]
        .mean()
        .reset_index()
    )

    avg_volume.rename(
        columns={
            "TTL_TRD_QNTY": "AVG_30D_VOLUME"
        },
        inplace=True
    )

    avg_volume.to_csv(
        f"avg_volume_{label}.csv",
        index=False
    )

    print(
        f"Created avg_volume_{label}.csv "
        f"using {len(files)} files."
    )

# Keep current dashboard working

avg_volume.to_csv(
    "avg_volume.csv",
    index=False
)
