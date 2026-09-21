```python
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Fundamentals",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Fundamentals")
st.caption("Screener-style company analysis")
st.caption("Data source: Screener.in :)")

st.divider()


# ─────────────────────────────────────────────
# LOAD SCREENER DATA
# ─────────────────────────────────────────────

@st.cache_data
def load_fundamentals():
    return pd.read_csv("fundamentals.csv")


df = load_fundamentals()

# Clean Screener column spacing
df.columns = (
    df.columns
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
)


# ─────────────────────────────────────────────
# FILTER OPTIONS
# ─────────────────────────────────────────────

field_aliases = {
    "P/E": "P/E",
    "P/B": "CMP / BV",
    "ROCE": "ROCE %",
    "ROE": "ROE 10Yr %",
    "Dividend Yield": "Div Yld %",
    "Market Cap": "Mar Cap Rs.Cr.",
    "Industry PBV": "Ind PBV",
}

display_fields = list(field_aliases.keys())


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────

if "filters" not in st.session_state:
    st.session_state.filters = []

if "selected_field" not in st.session_state:
    st.session_state.selected_field = "P/E"


# ─────────────────────────────────────────────
# FILTER BUILDER
# ─────────────────────────────────────────────

st.subheader("🔎 Build Your Screen")

col1, col2, col3, col4 = st.columns([3, 1.5, 2, 1.2])


with col1:

    selected_field = st.selectbox(
        "Metric",
        display_fields,
        index=display_fields.index(
            st.session_state.selected_field
        )
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

    # Remember the selected metric
    st.session_state.selected_field = selected_field

    csv_field = field_aliases[selected_field]

    # Make sure the CSV actually contains this column
    if csv_field not in df.columns:

        st.error(
            f"'{selected_field}' is not available in the current fundamentals.csv."
        )

    else:

        st.session_state.filters.append({
            "display": selected_field,
            "field": csv_field,
            "operator": selected_operator,
            "value": selected_value
        })

        st.toast(
            f"Added: {selected_field} {selected_operator} {selected_value}",
            icon="✅"
        )


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

            if st.button(
                "✕",
                key=f"remove_{i}"
            ):

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
    st.session_state.selected_field = "P/E"
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

        # Safety check
        if field not in result.columns:

            st.error(
                f"Column '{field}' was not found in fundamentals.csv."
            )
            continue

        # Convert the selected column to numbers
        numeric_column = pd.to_numeric(
            result[field],
            errors="coerce"
        )

        if operator == ">":
            result = result[numeric_column > value]

        elif operator == "<":
            result = result[numeric_column < value]

        elif operator == ">=":
            result = result[numeric_column >= value]

        elif operator == "<=":
            result = result[numeric_column <= value]

        elif operator == "=":
            result = result[numeric_column == value]

        elif operator == "!=":
            result = result[numeric_column != value]

    st.divider()

    st.subheader(
        f"📋 {len(result)} Companies Found"
    )

    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True
    )


# ─────────────────────────────────────────────
# RATIO GALLERY
# ─────────────────────────────────────────────

st.divider()

st.subheader("📚 Ratio Gallery")


st.markdown(
    """
    <div style="
        display:flex;
        gap:8px;
        margin-bottom:15px;
        font-size:20px;
    ">
        <b>+</b>
        <b>−</b>
        <b>÷</b>
        <b>×</b>
        <b>&gt;</b>
        <b>&lt;</b>
        <b>=</b>
        <b>AND</b>
        <b>OR</b>
    </div>
    """,
    unsafe_allow_html=True
)


gallery_tabs = st.tabs([
    "Most Used",
    "Balance Sheet",
    "Cash Flow",
    "Ratios",
    "Price"
])


# ─────────────────────────────────────────────
# GALLERY METRICS
# ─────────────────────────────────────────────

recent_metrics = [
    "Market Capitalization",
    "Price to Earning",
    "Dividend yield",
    "Price to book value",
    "Return on assets",
    "Debt to equity",
    "Return on equity",
    "Promoter holding",
    "Earnings yield",
    "Pledged percentage",
    "Industry PE",
    "Enterprise Value",
    "Number of equity shares",
    "Price to Quarterly Earning",
    "Book value",
    "Inventory turnover ratio",
    "Quick ratio",
    "Exports percentage",
    "Piotroski score",
    "G Factor",
    "Asset Turnover Ratio",
    "Financial leverage",
    "Number of Shareholders",
    "Unpledged promoter holding",
    "Return on invested capital",
    "Debtor days",
    "Industry PBV",
    "Credit rating",
    "Working Capital Days",
    "Earning Power",
    "Graham Number",
    "Cash Conversion Cycle",
    "Days Payable Outstanding",
    "Days Receivable Outstanding",
    "Days Inventory Outstanding",
    "Public holding",
    "FII holding",
    "Change in FII holding",
    "DII holding",
    "Change in DII holding"
]


historical_metrics = [
    "Average return on equity 5Years",
    "Average return on equity 3Years",
    "Number of equity shares 10years back",
    "Book value 3years back",
    "Book value 5years back",
    "Book value 10years back",
    "Inventory turnover ratio 3Years back",
    "Inventory turnover ratio 5Years back",
    "Inventory turnover ratio 7Years back",
    "Inventory turnover ratio 10Years back",
    "Exports percentage 3Years back",
    "Exports percentage 5Years back",
    "Average 5years dividend",
    "Average return on capital employed 3Years",
    "Average return on capital employed 5Years",
    "Average return on capital employed 7Years",
    "Average return on capital employed 10Years",
    "Working capital 3Years back",
    "Working capital 5Years back",
    "Working capital 7Years back",
    "Working capital 10Years back",
    "Debt 3Years back",
    "Debt 5Years back",
    "Debt 7Years back",
    "Debt 10Years back"
]


balance_sheet_metrics = [
    "Debt",
    "Equity capital",
    "Preference capital",
    "Reserves",
    "Secured loan",
    "Unsecured loan",
    "Balance sheet total",
    "Gross block",
    "Revaluation reserve",
    "Accumulated depreciation",
    "Net block",
    "Capital work in progress",
    "Investments",
    "Current assets",
    "Current liabilities",
    "Book value of unquoted investments",
    "Market value of quoted investments",
    "Contingent liabilities",
    "Total Assets",
    "Working capital",
    "Lease liabilities",
    "Inventory",
    "Trade receivables",
    "Face value",
    "Cash Equivalents",
    "Advance from Customers",
    "Trade Payables"
]


cash_flow_metrics = [
    "Cash from Operating Activity",
    "Cash from Investing Activity",
    "Cash from Financing Activity",
    "Net Cash Flow",
    "Free Cash Flow"
]


ratios_metrics = [
    "Price to Earning",
    "Price to book value",
    "Return on equity",
    "Return on capital employed",
    "Return on assets",
    "Debt to equity",
    "Dividend yield",
    "Earnings yield",
    "Inventory turnover ratio",
    "Quick ratio",
    "Asset Turnover Ratio",
    "Financial leverage",
    "Return on invested capital",
    "Debtor days",
    "Working Capital Days",
    "Cash Conversion Cycle",
    "Days Payable Outstanding",
    "Days Receivable Outstanding",
    "Days Inventory Outstanding",
    "Piotroski score",
    "G Factor"
]


price_metrics = [
    "Current Market Price",
    "Price to Earning",
    "Price to book value",
    "Dividend yield",
    "Industry PE",
    "Industry PBV",
    "Earnings yield",
    "Graham Number"
]


# ─────────────────────────────────────────────
# GALLERY → FILTER MAPPING
# ─────────────────────────────────────────────

gallery_map = {

    "Market Capitalization": "Market Cap",

    "Price to Earning": "P/E",

    "Price to book value": "P/B",

    "Return on equity": "ROE",

    "Return on capital employed": "ROCE",

    "Dividend yield": "Dividend Yield",

    "Industry PBV": "Industry PBV",

}


# ─────────────────────────────────────────────
# SHOW GALLERY BUTTONS
# ─────────────────────────────────────────────

def show_gallery_metrics(metrics, prefix):

    cols = st.columns(4)

    for i, metric in enumerate(metrics):

        with cols[i % 4]:

            if st.button(
                metric,
                key=f"{prefix}_{i}",
                use_container_width=True
            ):

                if metric in gallery_map:

                    st.session_state.selected_field = gallery_map[metric]

                    st.toast(
                        f"Selected: {metric}",
                        icon="✅"
                    )

                else:

                    st.toast(
                        f"{metric} isn't available in fundamentals.csv yet.",
                        icon="⚠️"
                    )

                st.rerun()


# ─────────────────────────────────────────────
# GALLERY TABS
# ─────────────────────────────────────────────

with gallery_tabs[0]:

    show_gallery_metrics(
        recent_metrics,
        "recent"
    )


with gallery_tabs[1]:

    show_gallery_metrics(
        balance_sheet_metrics,
        "balance"
    )


with gallery_tabs[2]:

    show_gallery_metrics(
        cash_flow_metrics,
        "cashflow"
    )


with gallery_tabs[3]:

    show_gallery_metrics(
        ratios_metrics,
        "ratios"
    )


with gallery_tabs[4]:

    show_gallery_metrics(
        price_metrics,
        "price"
    )
```
