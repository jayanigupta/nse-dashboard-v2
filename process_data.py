import pandas as pd

df = pd.read_csv("sec_bhavdata_full_02062026.csv")

print("Columns:")
print(df.columns.tolist())

print("\nFirst 5 rows:")
print(df.head())