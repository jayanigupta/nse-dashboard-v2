import streamlit as st
import pandas as pd

df = pd.read_csv("sec_bhavdata_full_02062026.csv")

df.columns = df.columns.str.strip()

st.title("NSE Delivery Dashboard")

search = st.text_input("Search Stock")

min_delivery = st.slider(
    "Minimum Delivery %",
    0,
    100,
    70
)

if search:
    df = df[
        df["SYMBOL"]
        .str.contains(search.upper())
    ]

df = df[df["DELIV_PER"] >= min_delivery]

df = df.sort_values(
    "DELIV_PER",
    ascending=False
)

st.dataframe(
    df[[
        "SYMBOL",
        "DELIV_PER",
        "TTL_TRD_QNTY"
    ]]
)