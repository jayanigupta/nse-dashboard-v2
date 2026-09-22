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


# =========================
# LOAD DATA
# =========================

@st.cache_data
def load_fundamentals():
    return pd.read_csv("fundamentals.csv")


df = load_fundamentals()

df.columns = (
    df.columns
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
)


# =========================
# FILTER OPTIONS
# =========================

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


# =========================
# SESSION STATE
# =========================

if "filters" not in st.session_state:
    st.session_state.filters = []

if "selected_field" not in st.session_state:
    st.session_state.selected_field = "P/E"


# =========================
# FILTER BUILDER
# =========================

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


# =========================
# ADD FILTER
# =========================

if add_filter:

    st.session_state.selected_field = selected_field

    csv_field = field_aliases[selected_field]

    if csv_field not in df.columns:

        st.error(
            f"{selected_field} is not available in the current data."
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


# =========================
# ACTIVE FILTERS
# =========================

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


# =========================
# RUN / CLEAR
# =========================

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


# =========================
# RUN FILTERS
# =========================

if run_screen:

    result = df.copy()

    for filter_item in st.session_state.filters:

        field = filter_item["field"]
        operator = filter_item["operator"]
        value = filter_item["value"]

        if field not in result.columns:

            st.error(f"Column not found: {field}")
            continue

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


    # =========================
    # RESULTS
    # =========================

    st.divider()

    st.subheader(
        f"📋 {len(result)} Companies Found"
    )


    # =========================
    # GROUPING OPTIONS
    # =========================

    st.markdown("### 📊 Group & Compare")


    # Available columns in current dataset
    available_groups = ["No Grouping"]

    if "Industry" in result.columns:
        available_groups.append("Industry")


    # Market cap grouping
    if "Mar Cap Rs.Cr." in result.columns:
        available_groups.append("Market Cap Size")


    # Price grouping
    if "CMP Rs." in result.columns:
        available_groups.append("Price Range")


    # P/E grouping
    if "P/E" in result.columns:
        available_groups.append("P/E Range")


    # P/B grouping
    if "CMP / BV" in result.columns:
        available_groups.append("P/B Range")


    # Dividend grouping
    if "Div Yld %" in result.columns:
        available_groups.append("Dividend Yield Range")


    # ROE grouping
    if "ROE 10Yr %" in result.columns:
        available_groups.append("ROE Range")


    # ROCE grouping
    if "ROCE %" in result.columns:
        available_groups.append("ROCE Range")


    # Quarterly growth
    if "Qtr Sales Var %" in result.columns:
        available_groups.append("Quarterly Sales Growth")


    if "Qtr Profit Var %" in result.columns:
        available_groups.append("Quarterly Profit Growth")


    group_by = st.selectbox(
        "Group by",
        available_groups
    )


    # =========================
    # NO GROUPING
    # =========================

    if group_by == "No Grouping":

        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True
        )


    # =========================
    # INDUSTRY
    # =========================

    elif group_by == "Industry":

        grouped = (
            result
            .groupby("Industry")
            .size()
            .reset_index(name="Companies")
            .sort_values(
                "Companies",
                ascending=False
            )
        )

        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    # =========================
    # MARKET CAP SIZE
    # =========================

    elif group_by == "Market Cap Size":

        result = result.copy()

        market_cap = pd.to_numeric(
            result["Mar Cap Rs.Cr."],
            errors="coerce"
        )


        def market_cap_category(value):

            if pd.isna(value):
                return "Unknown"

            if value >= 20000:
                return "Large Cap"

            elif value >= 5000:
                return "Mid Cap"

            else:
                return "Small Cap"


        result["Market Cap Size"] = market_cap.apply(
            market_cap_category
        )


        grouped = (
            result
            .groupby("Market Cap Size")
            .size()
            .reset_index(name="Companies")
        )


        order = [
            "Large Cap",
            "Mid Cap",
            "Small Cap",
            "Unknown"
        ]


        grouped["sort_order"] = grouped[
            "Market Cap Size"
        ].apply(
            lambda x: order.index(x)
            if x in order
            else 99
        )


        grouped = (
            grouped
            .sort_values("sort_order")
            .drop(columns="sort_order")
        )


        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    # =========================
    # PRICE RANGE
    # =========================

    elif group_by == "Price Range":

        price = pd.to_numeric(
            result["CMP Rs."],
            errors="coerce"
        )


        bins = [
            -float("inf"),
            100,
            500,
            1000,
            5000,
            float("inf")
        ]


        labels = [
            "Below ₹100",
            "₹100–500",
            "₹500–1,000",
            "₹1,000–5,000",
            "Above ₹5,000"
        ]


        grouped = (
            pd.cut(
                price,
                bins=bins,
                labels=labels
            )
            .value_counts()
            .reindex(labels, fill_value=0)
            .reset_index()
        )


        grouped.columns = [
            "Price Range",
            "Companies"
        ]


        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    # =========================
    # P/E RANGE
    # =========================

    elif group_by == "P/E Range":

        pe = pd.to_numeric(
            result["P/E"],
            errors="coerce"
        )


        bins = [
            -float("inf"),
            10,
            20,
            30,
            50,
            float("inf")
        ]


        labels = [
            "Below 10",
            "10–20",
            "20–30",
            "30–50",
            "Above 50"
        ]


        grouped = (
            pd.cut(
                pe,
                bins=bins,
                labels=labels
            )
            .value_counts()
            .reindex(labels, fill_value=0)
            .reset_index()
        )


        grouped.columns = [
            "P/E Range",
            "Companies"
        ]


        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    # =========================
    # P/B RANGE
    # =========================

    elif group_by == "P/B Range":

        pb = pd.to_numeric(
            result["CMP / BV"],
            errors="coerce"
        )


        bins = [
            -float("inf"),
            1,
            2,
            5,
            10,
            float("inf")
        ]


        labels = [
            "Below 1",
            "1–2",
            "2–5",
            "5–10",
            "Above 10"
        ]


        grouped = (
            pd.cut(
                pb,
                bins=bins,
                labels=labels
            )
            .value_counts()
            .reindex(labels, fill_value=0)
            .reset_index()
        )


        grouped.columns = [
            "P/B Range",
            "Companies"
        ]


        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    # =========================
    # DIVIDEND YIELD RANGE
    # =========================

    elif group_by == "Dividend Yield Range":

        dividend = pd.to_numeric(
            result["Div Yld %"],
            errors="coerce"
        )


        bins = [
            -float("inf"),
            1,
            2,
            4,
            6,
            float("inf")
        ]


        labels = [
            "Below 1%",
            "1–2%",
            "2–4%",
            "4–6%",
            "Above 6%"
        ]


        grouped = (
            pd.cut(
                dividend,
                bins=bins,
                labels=labels
            )
            .value_counts()
            .reindex(labels, fill_value=0)
            .reset_index()
        )


        grouped.columns = [
            "Dividend Yield Range",
            "Companies"
        ]


        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    # =========================
    # ROE RANGE
    # =========================

    elif group_by == "ROE Range":

        roe = pd.to_numeric(
            result["ROE 10Yr %"],
            errors="coerce"
        )


        bins = [
            -float("inf"),
            0,
            10,
            20,
            30,
            50,
            float("inf")
        ]


        labels = [
            "Negative",
            "0–10%",
            "10–20%",
            "20–30%",
            "30–50%",
            "Above 50%"
        ]


        grouped = (
            pd.cut(
                roe,
                bins=bins,
                labels=labels
            )
            .value_counts()
            .reindex(labels, fill_value=0)
            .reset_index()
        )


        grouped.columns = [
            "ROE Range",
            "Companies"
        ]


        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    # =========================
    # ROCE RANGE
    # =========================

    elif group_by == "ROCE Range":

        roce = pd.to_numeric(
            result["ROCE %"],
            errors="coerce"
        )


        bins = [
            -float("inf"),
            0,
            10,
            20,
            30,
            50,
            float("inf")
        ]


        labels = [
            "Negative",
            "0–10%",
            "10–20%",
            "20–30%",
            "30–50%",
            "Above 50%"
        ]


        grouped = (
            pd.cut(
                roce,
                bins=bins,
                labels=labels
            )
            .value_counts()
            .reindex(labels, fill_value=0)
            .reset_index()
        )


        grouped.columns = [
            "ROCE Range",
            "Companies"
        ]


        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    # =========================
    # QUARTERLY SALES GROWTH
    # =========================

    elif group_by == "Quarterly Sales Growth":

        growth = pd.to_numeric(
            result["Qtr Sales Var %"],
            errors="coerce"
        )


        bins = [
            -float("inf"),
            0,
            10,
            20,
            50,
            float("inf")
        ]


        labels = [
            "Negative",
            "0–10%",
            "10–20%",
            "20–50%",
            "Above 50%"
        ]


        grouped = (
            pd.cut(
                growth,
                bins=bins,
                labels=labels
            )
            .value_counts()
            .reindex(labels, fill_value=0)
            .reset_index()
        )


        grouped.columns = [
            "Quarterly Sales Growth",
            "Companies"
        ]


        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    # =========================
    # QUARTERLY PROFIT GROWTH
    # =========================

    elif group_by == "Quarterly Profit Growth":

        growth = pd.to_numeric(
            result["Qtr Profit Var %"],
            errors="coerce"
        )


        bins = [
            -float("inf"),
            0,
            10,
            20,
            50,
            float("inf")
        ]


        labels = [
            "Negative",
            "0–10%",
            "10–20%",
            "20–50%",
            "Above 50%"
        ]


        grouped = (
            pd.cut(
                growth,
                bins=bins,
                labels=labels
            )
            .value_counts()
            .reindex(labels, fill_value=0)
            .reset_index()
        )


        grouped.columns = [
            "Quarterly Profit Growth",
            "Companies"
        ]


        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    # =========================
    # MEDIAN COMPARISON
    # =========================

    st.divider()

    st.subheader("📐 Compare Against Median")

    st.caption(
        "Compare a metric against the median of the screened companies."
    )


    comparison_options = {}


    for display_name, csv_name in field_aliases.items():

        if csv_name in result.columns:

            comparison_options[
                display_name
            ] = csv_name


    # Add growth metrics
    if "Qtr Sales Var %" in result.columns:

        comparison_options[
            "Quarterly Sales Growth"
        ] = "Qtr Sales Var %"


    if "Qtr Profit Var %" in result.columns:

        comparison_options[
            "Quarterly Profit Growth"
        ] = "Qtr Profit Var %"


    if comparison_options and len(result) > 0:

        compare_metric = st.selectbox(
            "Compare metric",
            list(comparison_options.keys())
        )


        comparison_column = comparison_options[
            compare_metric
        ]


        comparison_values = pd.to_numeric(
            result[comparison_column],
            errors="coerce"
        )


        median_value = comparison_values.median()


        if pd.isna(median_value):

            st.warning(
                "There isn't enough numeric data to calculate the median."
            )

        else:

            st.metric(
                f"Median {compare_metric}",
                f"{median_value:.2f}"
            )


            comparison_table = result[
                ["Company", comparison_column]
            ].copy()


            comparison_table[
                compare_metric
            ] = pd.to_numeric(
                comparison_table[
                    comparison_column
                ],
                errors="coerce"
            )


            comparison_table = comparison_table.drop(
                columns=[comparison_column]
            )


            comparison_table[
                "vs Median"
            ] = comparison_table[
                compare_metric
            ].apply(
                lambda x:
                "🟢 Above"
                if x > median_value
                else (
                    "🔴 Below"
                    if x < median_value
                    else "⚪ Median"
                )
                if pd.notna(x)
                else "—"
            )


            comparison_table[
                "Difference from Median"
            ] = (
                comparison_table[
                    compare_metric
                ] - median_value
            ).round(2)


            comparison_table = comparison_table.sort_values(
                compare_metric,
                ascending=False,
                na_position="last"
            )


            st.dataframe(
                comparison_table,
                use_container_width=True,
                hide_index=True
            )


# =========================
# RATIO GALLERY
# =========================

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


# =========================
# GALLERY METRICS
# =========================

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


# =========================
# GALLERY MAPPING
# =========================

gallery_map = {
    "Market Capitalization": "Market Cap",
    "Price to Earning": "P/E",
    "Price to book value": "P/B",
    "Return on equity": "ROE",
    "Return on capital employed": "ROCE",
    "Dividend yield": "Dividend Yield",
    "Industry PBV": "Industry PBV",
}


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

                    st.session_state.selected_field = gallery_map[
                        metric
                    ]

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


# =========================
# SHOW GALLERY
# =========================

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
