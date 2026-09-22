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

if "screen_result" not in st.session_state:
    st.session_state.screen_result = None

if "group_by" not in st.session_state:
    st.session_state.group_by = "No Grouping"

if "compare_metric" not in st.session_state:
    st.session_state.compare_metric = None


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


# =========================
# CLEAR
# =========================

if clear_filters:

    st.session_state.filters = []
    st.session_state.selected_field = "P/E"
    st.session_state.screen_result = None

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

    # SAVE SCREENED RESULT
    st.session_state.screen_result = result


# =========================
# RESULTS
# =========================

if st.session_state.screen_result is not None:

    result = st.session_state.screen_result.copy()

    st.divider()

    st.subheader(
        f"📋 {len(result)} Companies Found"
    )


    # =========================
    # GROUPING
    # =========================

    st.markdown("### 📊 Group & Compare")

    available_groups = [
        "No Grouping"
    ]

    if "Industry" in result.columns:
        available_groups.append("Industry")

    if "Mar Cap Rs.Cr." in result.columns:
        available_groups.append("Market Cap Size")

    if "CMP Rs." in result.columns:
        available_groups.append("Price Range")

    if "P/E" in result.columns:
        available_groups.append("P/E Range")

    if "CMP / BV" in result.columns:
        available_groups.append("P/B Range")

    if "Div Yld %" in result.columns:
        available_groups.append("Dividend Yield Range")

    if "ROE 10Yr %" in result.columns:
        available_groups.append("ROE Range")

    if "ROCE %" in result.columns:
        available_groups.append("ROCE Range")

    if "Qtr Sales Var %" in result.columns:
        available_groups.append("Quarterly Sales Growth")

    if "Qtr Profit Var %" in result.columns:
        available_groups.append("Quarterly Profit Growth")


    # IMPORTANT:
    # Use the current selection as the widget key/value.
    group_by = st.selectbox(
        "Group by",
        available_groups,
        key="group_by"
    )


    # =========================
    # GROUP RESULT
    # =========================

    if group_by == "No Grouping":

        st.dataframe(
            result,
            use_container_width=True,
            hide_index=True
        )


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


    elif group_by == "Market Cap Size":

        market_cap = pd.to_numeric(
            result["Mar Cap Rs.Cr."],
            errors="coerce"
        )

        result["Market Cap Size"] = pd.cut(
            market_cap,
            bins=[
                -float("inf"),
                5000,
                20000,
                float("inf")
            ],
            labels=[
                "Small Cap",
                "Mid Cap",
                "Large Cap"
            ]
        )

        grouped = (
            result
            .groupby(
                "Market Cap Size",
                observed=False
            )
            .size()
            .reset_index(name="Companies")
        )

        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    elif group_by == "Price Range":

        price = pd.to_numeric(
            result["CMP Rs."],
            errors="coerce"
        )

        result["Price Range"] = pd.cut(
            price,
            bins=[
                -float("inf"),
                100,
                500,
                1000,
                5000,
                float("inf")
            ],
            labels=[
                "Below ₹100",
                "₹100–500",
                "₹500–1,000",
                "₹1,000–5,000",
                "Above ₹5,000"
            ]
        )

        grouped = (
            result
            .groupby(
                "Price Range",
                observed=False
            )
            .size()
            .reset_index(name="Companies")
        )

        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    elif group_by == "P/E Range":

        pe = pd.to_numeric(
            result["P/E"],
            errors="coerce"
        )

        result["P/E Range"] = pd.cut(
            pe,
            bins=[
                -float("inf"),
                10,
                20,
                30,
                50,
                float("inf")
            ],
            labels=[
                "Below 10",
                "10–20",
                "20–30",
                "30–50",
                "Above 50"
            ]
        )

        grouped = (
            result
            .groupby(
                "P/E Range",
                observed=False
            )
            .size()
            .reset_index(name="Companies")
        )

        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    elif group_by == "P/B Range":

        pb = pd.to_numeric(
            result["CMP / BV"],
            errors="coerce"
        )

        result["P/B Range"] = pd.cut(
            pb,
            bins=[
                -float("inf"),
                1,
                2,
                5,
                10,
                float("inf")
            ],
            labels=[
                "Below 1",
                "1–2",
                "2–5",
                "5–10",
                "Above 10"
            ]
        )

        grouped = (
            result
            .groupby(
                "P/B Range",
                observed=False
            )
            .size()
            .reset_index(name="Companies")
        )

        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    elif group_by == "Dividend Yield Range":

        dividend = pd.to_numeric(
            result["Div Yld %"],
            errors="coerce"
        )

        result["Dividend Yield Range"] = pd.cut(
            dividend,
            bins=[
                -float("inf"),
                1,
                2,
                4,
                6,
                float("inf")
            ],
            labels=[
                "Below 1%",
                "1–2%",
                "2–4%",
                "4–6%",
                "Above 6%"
            ]
        )

        grouped = (
            result
            .groupby(
                "Dividend Yield Range",
                observed=False
            )
            .size()
            .reset_index(name="Companies")
        )

        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    elif group_by == "ROE Range":

        roe = pd.to_numeric(
            result["ROE 10Yr %"],
            errors="coerce"
        )

        result["ROE Range"] = pd.cut(
            roe,
            bins=[
                -float("inf"),
                0,
                10,
                20,
                30,
                50,
                float("inf")
            ],
            labels=[
                "Negative",
                "0–10%",
                "10–20%",
                "20–30%",
                "30–50%",
                "Above 50%"
            ]
        )

        grouped = (
            result
            .groupby(
                "ROE Range",
                observed=False
            )
            .size()
            .reset_index(name="Companies")
        )

        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    elif group_by == "ROCE Range":

        roce = pd.to_numeric(
            result["ROCE %"],
            errors="coerce"
        )

        result["ROCE Range"] = pd.cut(
            roce,
            bins=[
                -float("inf"),
                0,
                10,
                20,
                30,
                50,
                float("inf")
            ],
            labels=[
                "Negative",
                "0–10%",
                "10–20%",
                "20–30%",
                "30–50%",
                "Above 50%"
            ]
        )

        grouped = (
            result
            .groupby(
                "ROCE Range",
                observed=False
            )
            .size()
            .reset_index(name="Companies")
        )

        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    elif group_by == "Quarterly Sales Growth":

        growth = pd.to_numeric(
            result["Qtr Sales Var %"],
            errors="coerce"
        )

        result["Quarterly Sales Growth"] = pd.cut(
            growth,
            bins=[
                -float("inf"),
                0,
                10,
                20,
                50,
                float("inf")
            ],
            labels=[
                "Negative",
                "0–10%",
                "10–20%",
                "20–50%",
                "Above 50%"
            ]
        )

        grouped = (
            result
            .groupby(
                "Quarterly Sales Growth",
                observed=False
            )
            .size()
            .reset_index(name="Companies")
        )

        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )


    elif group_by == "Quarterly Profit Growth":

        growth = pd.to_numeric(
            result["Qtr Profit Var %"],
            errors="coerce"
        )

        result["Quarterly Profit Growth"] = pd.cut(
            growth,
            bins=[
                -float("inf"),
                0,
                10,
                20,
                50,
                float("inf")
            ],
            labels=[
                "Negative",
                "0–10%",
                "10–20%",
                "20–50%",
                "Above 50%"
            ]
        )

        grouped = (
            result
            .groupby(
                "Quarterly Profit Growth",
                observed=False
            )
            .size()
            .reset_index(name="Companies")
        )

        st.dataframe(
            grouped,
            use_container_width=True,
            hide_index=True
        )

# =========================
# DAILY STATISTICS
# =========================

if st.session_state.screen_result is not None:

    result = st.session_state.screen_result.copy()

    st.divider()

    st.subheader("📊 Daily Statistics")

    st.caption(
        "Compare multiple financial metrics across the screened companies."
    )


    # =========================
    # AVAILABLE NUMERIC COLUMNS
    # =========================

    excluded_columns = [
        "S.No.",
        "Company"
    ]

    numeric_metrics = {}

    for column in result.columns:

        if column in excluded_columns:
            continue

        numeric_values = pd.to_numeric(
            result[column],
            errors="coerce"
        )

        # Only include columns that contain numeric data
        if numeric_values.notna().sum() > 0:

            numeric_metrics[column] = column


    # =========================
    # FRIENDLY NAMES
    # =========================

    metric_names = {
        "P/E": "P/E",
        "CMP / BV": "P/B",
        "ROCE %": "ROCE",
        "ROE 10Yr %": "ROE",
        "Div Yld %": "Dividend Yield",
        "Mar Cap Rs.Cr.": "Market Cap",
        "CMP Rs.": "Current Market Price",
        "Qtr Sales Var %": "Quarterly Sales Growth",
        "Qtr Profit Var %": "Quarterly Profit Growth",
        "Ind PBV": "Industry PBV",
    }


    display_metrics = {
        metric_names.get(column, column): column
        for column in numeric_metrics
    }


    # =========================
    # SELECT METRICS
    # =========================

    st.markdown("### 📌 Metrics")

    selected_metrics = st.multiselect(
        "Choose the metrics you want in the table",
        list(display_metrics.keys()),
        default=[
            metric
            for metric in [
                "ROCE",
                "P/B"
            ]
            if metric in display_metrics
        ],
        key="daily_statistics_metrics"
    )


    if selected_metrics:

        # =========================
        # STATISTICS TO DISPLAY
        # =========================

        st.markdown("### 🔘 What do you want to display?")

        statistic_options = [
            "Value",
            "Mean",
            "Median",
            "Minimum",
            "Maximum",
            "25th Percentile",
            "75th Percentile",
            "Standard Deviation",
            "IQR",
            "Range",
            "Rank",
            "Percentile",
            "Difference from Mean",
            "Difference from Median",
            "vs Mean",
            "vs Median",
            "Top 25%",
            "Bottom 25%"
        ]


        if "selected_daily_stats" not in st.session_state:

            st.session_state.selected_daily_stats = [
                "Value",
                "Median",
                "vs Median"
            ]


        # =========================
        # STATISTIC BUTTONS
        # =========================

        button_cols = st.columns(4)

        for i, option in enumerate(statistic_options):

            with button_cols[i % 4]:

                is_selected = (
                    option
                    in st.session_state.selected_daily_stats
                )

                button_text = (
                    "✓ " if is_selected else ""
                ) + option


                if st.button(
                    button_text,
                    key=f"daily_stat_button_{i}",
                    use_container_width=True
                ):

                    if option in st.session_state.selected_daily_stats:

                        st.session_state.selected_daily_stats.remove(
                            option
                        )

                    else:

                        st.session_state.selected_daily_stats.append(
                            option
                        )

                    st.rerun()


        selected_stats = (
            st.session_state.selected_daily_stats
        )


        # =========================
        # BUILD COMPARISON TABLE
        # =========================

        comparison_table = pd.DataFrame({
            "Company": result["Company"]
        })


        # =========================
        # PROCESS EACH METRIC
        # =========================

        for metric in selected_metrics:

            column = display_metrics[metric]

            values = pd.to_numeric(
                result[column],
                errors="coerce"
            )


            # -------------------------
            # BASIC STATISTICS
            # -------------------------

            valid_values = values.dropna()

            if len(valid_values) == 0:
                continue


            mean_value = valid_values.mean()
            median_value = valid_values.median()
            minimum = valid_values.min()
            maximum = valid_values.max()

            q1 = valid_values.quantile(0.25)
            q3 = valid_values.quantile(0.75)

            std_dev = valid_values.std()

            iqr = q3 - q1
            value_range = maximum - minimum


            # -------------------------
            # VALUE
            # -------------------------

            if "Value" in selected_stats:

                comparison_table[metric] = (
                    values.round(2)
                )


            # -------------------------
            # MEAN
            # -------------------------

            if "Mean" in selected_stats:

                comparison_table[
                    f"{metric} Mean"
                ] = round(mean_value, 2)


            # -------------------------
            # MEDIAN
            # -------------------------

            if "Median" in selected_stats:

                comparison_table[
                    f"{metric} Median"
                ] = round(median_value, 2)


            # -------------------------
            # MINIMUM
            # -------------------------

            if "Minimum" in selected_stats:

                comparison_table[
                    f"{metric} Min"
                ] = round(minimum, 2)


            # -------------------------
            # MAXIMUM
            # -------------------------

            if "Maximum" in selected_stats:

                comparison_table[
                    f"{metric} Max"
                ] = round(maximum, 2)


            # -------------------------
            # 25TH PERCENTILE
            # -------------------------

            if "25th Percentile" in selected_stats:

                comparison_table[
                    f"{metric} Q1"
                ] = round(q1, 2)


            # -------------------------
            # 75TH PERCENTILE
            # -------------------------

            if "75th Percentile" in selected_stats:

                comparison_table[
                    f"{metric} Q3"
                ] = round(q3, 2)


            # -------------------------
            # STANDARD DEVIATION
            # -------------------------

            if "Standard Deviation" in selected_stats:

                comparison_table[
                    f"{metric} Std Dev"
                ] = round(std_dev, 2)


            # -------------------------
            # IQR
            # -------------------------

            if "IQR" in selected_stats:

                comparison_table[
                    f"{metric} IQR"
                ] = round(iqr, 2)


            # -------------------------
            # RANGE
            # -------------------------

            if "Range" in selected_stats:

                comparison_table[
                    f"{metric} Range"
                ] = round(value_range, 2)


            # -------------------------
            # RANK
            # -------------------------

            if "Rank" in selected_stats:

                comparison_table[
                    f"{metric} Rank"
                ] = (
                    values.rank(
                        ascending=False,
                        method="min"
                    )
                )


            # -------------------------
            # PERCENTILE
            # -------------------------

            if "Percentile" in selected_stats:

                comparison_table[
                    f"{metric} Percentile"
                ] = (
                    values.rank(
                        pct=True,
                        method="average"
                    ) * 100
                ).round(1)


            # -------------------------
            # DIFFERENCE FROM MEAN
            # -------------------------

            if "Difference from Mean" in selected_stats:

                comparison_table[
                    f"{metric} Δ Mean"
                ] = (
                    values - mean_value
                ).round(2)


            # -------------------------
            # DIFFERENCE FROM MEDIAN
            # -------------------------

            if "Difference from Median" in selected_stats:

                comparison_table[
                    f"{metric} Δ Median"
                ] = (
                    values - median_value
                ).round(2)


            # -------------------------
            # VS MEAN
            # -------------------------

            if "vs Mean" in selected_stats:

                comparison_table[
                    f"{metric} vs Mean"
                ] = values.apply(
                    lambda x:
                    "🟢 Above"
                    if pd.notna(x) and x > mean_value
                    else (
                        "🔴 Below"
                        if pd.notna(x) and x < mean_value
                        else (
                            "⚪ Mean"
                            if pd.notna(x)
                            else "—"
                        )
                    )
                )


            # -------------------------
            # VS MEDIAN
            # -------------------------

            if "vs Median" in selected_stats:

                comparison_table[
                    f"{metric} vs Median"
                ] = values.apply(
                    lambda x:
                    "🟢 Above"
                    if pd.notna(x) and x > median_value
                    else (
                        "🔴 Below"
                        if pd.notna(x) and x < median_value
                        else (
                            "⚪ Median"
                            if pd.notna(x)
                            else "—"
                        )
                    )
                )


            # -------------------------
            # TOP 25%
            # -------------------------

            if "Top 25%" in selected_stats:

                comparison_table[
                    f"{metric} Top 25%"
                ] = values.apply(
                    lambda x:
                    "⭐ Top 25%"
                    if pd.notna(x) and x >= q3
                    else "—"
                )


            # -------------------------
            # BOTTOM 25%
            # -------------------------

            if "Bottom 25%" in selected_stats:

                comparison_table[
                    f"{metric} Bottom 25%"
                ] = values.apply(
                    lambda x:
                    "🔻 Bottom 25%"
                    if pd.notna(x) and x <= q1
                    else "—"
                )


        # =========================
        # DISPLAY TABLE
        # =========================

        st.markdown("### 📋 Company Comparison")

        comparison_table = comparison_table[
            comparison_table["Company"].notna()
            & (comparison_table["Company"].astype(str).str.strip() != "")
        ]


        st.dataframe(
            comparison_table,
            use_container_width=True,
            hide_index=True
        )


        # =========================
        # DAILY SUMMARY
        # =========================

        st.markdown("### 📈 Daily Summary")

        summary_rows = []

        for metric in selected_metrics:

            column = display_metrics[metric]

            values = pd.to_numeric(
                result[column],
                errors="coerce"
            ).dropna()

            if len(values) == 0:
                continue

            summary_rows.append({
                "Metric": metric,
                "Companies": len(values),
                "Mean": round(values.mean(), 2),
                "Median": round(values.median(), 2),
                "Min": round(values.min(), 2),
                "25th Percentile": round(
                    values.quantile(0.25),
                    2
                ),
                "75th Percentile": round(
                    values.quantile(0.75),
                    2
                ),
                "Max": round(values.max(), 2),
                "Std Dev": round(values.std(), 2),
                "IQR": round(
                    values.quantile(0.75)
                    - values.quantile(0.25),
                    2
                )
            })


        summary_table = pd.DataFrame(
            summary_rows
        )


        st.dataframe(
            summary_table,
            use_container_width=True,
            hide_index=True
        )


    else:

        st.info(
            "Select at least one metric above."
        )

else:

    st.info(
        "Run a screen first to calculate daily statistics."
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
