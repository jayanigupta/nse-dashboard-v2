import streamlit as st

st.set_page_config(
    page_title="Fundamentals",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Fundamentals")
st.caption("Screener-style company analysis")

st.divider()

# ─────────────────────────────────────────────
# QUERY
# ─────────────────────────────────────────────

st.subheader("Query")

query = st.text_area(
    "Enter your query",
    placeholder="""Example:
Market Capitalization > 10000
AND Price to Earning < 25
AND Price to Book Value < 3
AND Return on Equity > 15""",
    height=130,
    label_visibility="collapsed"
)

col1, col2 = st.columns([1, 5])

with col1:
    run_query = st.button(
        "🔍 Run Query",
        use_container_width=True
    )

st.divider()

if run_query:
    if query.strip():
        st.success(f"Query received:\n\n{query}")
    else:
        st.warning("Enter a query first.")
