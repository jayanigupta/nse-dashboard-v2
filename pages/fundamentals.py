import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Fundamentals",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Fundamentals")
st.caption("Screener-style company analysis")

st.divider()

# ─────────────────────────────────────────────
# SAMPLE DATA — TEMPORARY
# ─────────────────────────────────────────────

sample_data = {
    "Company": [
        "Reliance Industries",
        "TCS",
        "Infosys",
        "ITC",
        "HDFC Bank",
    ],
    "Market Capitalization": [1800000, 1200000, 700000, 550000, 900000],
    "Price to Earning": [24.5, 28.2, 22.1, 25.3, 19.4],
    "Price to Book Value": [2.8, 12.4, 7.1, 8.2, 2.5],
    "Return on Equity": [9.5, 51.2, 32.4, 27.8, 16.5],
    "Return on Capital Employed": [10.2, 45.1, 38.7, 35.2, 8.9],
    "Debt to Equity": [0.42, 0.08, 0.12, 0.01, 0.75],
    "Dividend Yield": [0.35, 1.15, 2.10, 3.20, 1.05],
}

df = pd.DataFrame(sample_data)


# ─────────────────────────────────────────────
# FILTER OPTIONS
# ─────────────────────────────────────────────

field_aliases = {
    "P/E": "Price to Earning",
    "P/B": "Price to Book Value",
    "ROE": "Return on Equity",
    "ROCE": "Return on Capital Employed",
    "Debt / Equity": "Debt to Equity",
    "Dividend Yield": "Dividend Yield",
    "Market Cap": "Market Capitalization",
}

display_fields = list(field_aliases.keys())


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

if "filters" not in st.session_state:
    st.session_state.filters = []


# ─────────────────────────────────────────────
# FILTER BUILDER
# ─────────────────────────────────────────────

st.subheader("🔎 Build Your Screen")

col1, col2, col3, col4 = st.columns([3, 1.5, 2, 1.2])

with col1:
    selected_field = st.selectbox(
        "Metric",
        display_fields
    )

with col2:
    selected_operator = st.selectbox(
        "Condition",
        [">", "<", ">=", "<=", "=", "!="]
    )

with col3:
    selected_value = st.number_input(
        "Value",
        value=0.0,
        step=1.0
    )

with col4:
    st.write("")
    st.write("")
    add_filter = st.button(
        "➕ Add",
        use_container_width=True
    )


# ─────────────────────────────────────────────
# ADD FILTER
# ─────────────────────────────────────────────

if add_filter:

    st.session_state.filters.append({
        "display": selected_field,
        "field": field_aliases[selected_field],
        "operator": selected_operator,
        "value": selected_value
    })


# ─────────────────────────────────────────────
# SHOW ACTIVE FILTERS
# ─────────────────────────────────────────────

if st.session_state.filters:

    st.markdown("### Active Filters")

    for i, filter_item in enumerate(st.session_state.filters):

        col1, col2 = st.columns([8, 1])

        with col1:
            st.info(
                f"{filter_item['display']} "
                f"{filter_item['operator']} "
                f"{filter_item['value']}"
            )

        with col2:
            if st.button("✕", key=f"remove_{i}"):
                st.session_state.filters.pop(i)
                st.rerun()


# ─────────────────────────────────────────────
# BUTTONS
# ─────────────────────────────────────────────

col_run, col_clear = st.columns([2, 1])

with col_run:
    run_screen = st.button(
        "🔍 Run Screen",
        use_container_width=True
    )

with col_clear:
    clear_filters = st.button(
        "🗑 Clear",
        use_container_width=True
    )

if clear_filters:
    st.session_state.filters = []
    st.rerun()


# ─────────────────────────────────────────────
# RUN FILTERS
# ─────────────────────────────────────────────

if run_screen:

    result = df.copy()

    for filter_item in st.session_state.filters:

        field = filter_item["field"]
        operator = filter_item["operator"]
        value = filter_item["value"]

        if operator == ">":
            result = result[result[field] > value]

        elif operator == "<":
            result = result[result[field] < value]

        elif operator == ">=":
            result = result[result[field] >= value]

        elif operator == "<=":
            result = result[result[field] <= value]

        elif operator == "=":
            result = result[result[field] == value]

        elif operator == "!=":
            result = result[result[field] != value]

    st.divider()

    st.subheader(f"📋 {len(result)} Companies Found")

    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True
    )
