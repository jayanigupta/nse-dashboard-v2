import streamlit as st
import pandas as pd
import os

st.set_page_config(
    page_title="Fundamentals",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Fundamentals")
st.caption("Screener-style company analysis")
st.caption("Data source: Screener.in, NSE, Yahoo Finance")

st.divider()


# =========================
# LOAD FUNDAMENTALS DATA
# =========================

@st.cache_data
def load_fundamentals(file_modified_time):

    
    fundamentals = pd.read_csv(
        "fundamentals.csv"
    )

    # =================================================
    # LOAD MARKET LENS
    # =================================================

    if "marketlens.csv" in os.listdir("."):

        marketlens = pd.read_csv(
            "marketlens.csv"
        )

        marketlens.columns = (
            marketlens.columns.str.strip()
        )

        # Extract NSE symbol from:
        # Company Name (SYMBOL)

        if "Company" in marketlens.columns:

            marketlens["Symbol"] = (
                marketlens["Company"]
                .astype(str)
                .str.extract(
                    r"\(([^()]+)\)\s*$"
                )[0]
                .astype(str)
                .str.strip()
                .str.upper()
            )

        marketlens = marketlens.drop_duplicates(
            subset=["Symbol"]
        )

        marketlens_display_columns = [
            "Symbol",
            "Sector",
            "Sub Sector",
            "1D Return (%)",
            "1W Return (%)",
            "1M Return (%)",
            "Volume",
        ]

        marketlens_display_columns = [
            column
            for column in marketlens_display_columns
            if column in marketlens.columns
        ]

        fundamentals = fundamentals.merge(
            marketlens[
                marketlens_display_columns
            ],
            on="Symbol",
            how="left",
            suffixes=("", "_ML")
        )

    # =================================================
    # LOAD FORECAST DATA
    # =================================================

    if "forecast.csv" in os.listdir("."):

        forecast = pd.read_csv(
            "forecast.csv"
        )

        forecast.columns = (
            forecast.columns.str.strip()
        )

        forecast_columns = [
            "Symbol",
            "Forecast EPS",
            "Forecast EPS Growth",
            "Forward P/E",
            "Forecast Revenue",
            "Forecast Revenue Growth",
        ]

        forecast_columns = [
            column
            for column in forecast_columns
            if column in forecast.columns
        ]

        fundamentals = fundamentals.merge(
            forecast[forecast_columns],
            on="Symbol",
            how="left"
        )

    return fundamentals

df = load_fundamentals(
    os.path.getmtime("fundamentals.csv")
)    

# =========================
# CLEAN + NORMALIZE INDUSTRY
# =========================

df.columns = df.columns.str.strip()

if "Industry" in df.columns:
    df["Industry"] = (
        df["Industry"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Merge similar industry names
    industry_normalization = {
        # Information Technology
        "Information Technology Services": "Information Technology",

        # Textiles
        "Textile Manufacturing": "Textiles",

        # Telecommunications
        "Telecommunication": "Telecom Services",
        "Telecom Services": "Telecom Services",

        # Real estate
        "Real Estate - Development": "Real Estate",
        "Real Estate Services": "Real Estate",
        "Realty": "Real Estate",

        # Industrial machinery
        "Engineering - Industrial Equipments": "Industrial Machinery",

        # Electronics
        "Electronics - Components": "Electronics & Components",

        # Communication equipment
        "Communication Equipment": "Telecommunications - Equipment",

        # Financial services
        "Financial Services - Misc": "Financial Services",

        # Chemicals
        "Commodity Chemicals": "Chemicals",
    }

    df["Industry"] = df["Industry"].replace(industry_normalization)

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

    "Forecast EPS": "Forecast EPS",
    "Forecast EPS Growth": "Forecast EPS Growth",
    "Forward P/E": "Forward P/E",
    "Forecast Revenue": "Forecast Revenue",
    "Forecast Revenue Growth": "Forecast Revenue Growth",
}

display_fields = list(field_aliases.keys())

# =========================
# SESSION STATE
# =========================

if "clear_filters_requested" not in st.session_state:
    st.session_state.clear_filters_requested = False

if "filters" not in st.session_state:
    st.session_state.filters = []

if "selected_field" not in st.session_state:
    st.session_state.selected_field = "None"

if "filter_metric" not in st.session_state:
    st.session_state.filter_metric = "None"

if "screen_result" not in st.session_state:
    st.session_state.screen_result = None

if "group_by" not in st.session_state:
    st.session_state.group_by = "No Grouping"

if "industry_selected_metrics" not in st.session_state:
    st.session_state.industry_selected_metrics = []

if "industry_selected_statistics" not in st.session_state:
    st.session_state.industry_selected_statistics = []

if "industry_company_selection" not in st.session_state:
    st.session_state.industry_company_selection = "None"

if "industry_explorer_selection" not in st.session_state:
    st.session_state.industry_explorer_selection = "All Industries"

if "selected_daily_stats" not in st.session_state:
    st.session_state.selected_daily_stats = [
        "Value",
        "Median",
        "vs Median"
    ]


# =========================
# FILTER BUILDER
# =========================

st.subheader("🔎 Build Your Screen")

col1, col2, col3, col4 = st.columns(
    [3, 1.5, 2, 1.2]
)


with col1:

    # =========================
    # RESET FILTER WIDGETS
    # =========================

    if st.session_state.clear_filters_requested:

        st.session_state.filters = []
        st.session_state.screen_result = None

        st.session_state.selected_field = "None"
        st.session_state.filter_operator = ">"
        st.session_state.filter_value = 0.0

        st.session_state.group_by = "No Grouping"

        st.session_state.industry_company_selection = "None"
        st.session_state.industry_explorer_selection = "All Industries"
        st.session_state.industry_selected_metrics = []
        st.session_state.industry_selected_statistics = []

        st.session_state.selected_daily_stats = [
            "Value",
            "Median",
            "vs Median"
        ]

        st.session_state.clear_filters_requested = False

    selected_field = st.selectbox(
        "Metric",
        ["None"] + display_fields,
        index=0,
        key="filter_metric"
    )


with col2:

    selected_operator = st.selectbox(
        "Condition",
        [">", "<", ">=", "<=", "=", "!="],
        key="filter_operator"
    )


with col3:
    selected_value = st.number_input(
        "Value",
        value=0.0,
        step=1.0,
        key="filter_value"
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
            "value": float(selected_value)
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

    for i, filter_item in enumerate(
        st.session_state.filters
    ):

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

    st.session_state.clear_filters_requested = True

    st.rerun()

# =========================
# RUN FILTERS
# =========================

if run_screen:

    result = df.copy()

    for filter_item in st.session_state.filters:

        field = filter_item["field"]
        operator = filter_item["operator"]
        value = float(filter_item["value"])

        if field not in result.columns:

            st.error(
                f"Column not found: {field}"
            )

            continue

        # IMPORTANT:
        # Always convert the selected column to numeric
        # BEFORE applying the filter.

        numeric_column = pd.to_numeric(
            result[field],
            errors="coerce"
        )

        if operator == ">":

            mask = numeric_column > value

        elif operator == "<":

            mask = numeric_column < value

        elif operator == ">=":

            mask = numeric_column >= value

        elif operator == "<=":

            mask = numeric_column <= value

        elif operator == "=":

            mask = numeric_column == value

        elif operator == "!=":

            mask = numeric_column != value

        else:

            mask = pd.Series(
                True,
                index=result.index
            )

        # Apply the mask to the dataframe itself
        result = result.loc[mask].copy()

    st.session_state.screen_result = result

    # Reset industry comparison when a new screen is run
    st.session_state.peer_selected_metrics = []
    st.session_state.peer_selected_stats = ["Value"]


# =========================
# RESULTS
# =========================

if st.session_state.screen_result is not None:

    result = (
        st.session_state.screen_result
        .copy()
    )

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
        available_groups.append(
            "Dividend Yield Range"
        )

    if "ROE 10Yr %" in result.columns:
        available_groups.append(
            "ROE Range"
        )

    if "ROCE %" in result.columns:
        available_groups.append(
            "ROCE Range"
        )

    if "Qtr Sales Var %" in result.columns:
        available_groups.append(
            "Quarterly Sales Growth"
        )

    if "Qtr Profit Var %" in result.columns:
        available_groups.append(
            "Quarterly Profit Growth"
        )


    group_by = st.selectbox(
        "Group by",
        available_groups,
        key="group_by"
    )


    # =========================
    # GROUP RESULT
    # =========================

    if group_by == "No Grouping":

        table_columns = [
            "Company",
            "Symbol",
            "Industry",
            "Sector",
            "Sub Sector",
            "CMP Rs.",
            "P/E",
            "Mar Cap Rs.Cr.",
            "Div Yld %",
            "1D Return (%)",
            "1W Return (%)",
            "1M Return (%)",
            "Volume",
            "ROCE %",
            "ROE 10Yr %",
            "CMP / BV",
            "Ind PBV",
        ]

        table_columns = [
            column
            for column in table_columns
            if column in result.columns
        ]

        display_result = result[
            table_columns
        ].copy()

        st.dataframe(
            display_result,
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


# =========================================================
# INDUSTRY EXPLORER
# =========================================================

if st.session_state.screen_result is not None:

    st.divider()

    st.subheader("🏭 Industry Explorer")

    st.caption(
        "Compare companies using industry peers, metrics, and statistics."
    )

    # =========================================================
    # START FROM SCREENED RESULTS
    # =========================================================

    industry_data = st.session_state.screen_result.copy()

    if "Industry" not in industry_data.columns:

        st.warning(
            "Industry data is not available for the current companies."
        )

    else:

        industry_data["Industry"] = (
            industry_data["Industry"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        industry_data = industry_data[
            (industry_data["Industry"] != "")
            & (industry_data["Industry"].str.lower() != "nan")
        ].copy()

        if len(industry_data) == 0:

            st.warning(
                "No industry information is available."
            )

        else:

            # =========================
            # COMPANY SEARCH
            # =========================

            company_options = ["None"] + sorted(
                industry_data["Company"].dropna().astype(str).unique().tolist()
            )

            selected_peer_company = st.selectbox(
                "🏢 Search / Select Company",
                company_options,
                index=0,
                key="industry_company_selection"
            )
            # =========================
            # INDUSTRY SEARCH
            # =========================

            industry_options = ["All Industries"] + sorted(
                industry_data["Industry"]
                .dropna()
                .astype(str)
                .str.strip()
                .loc[lambda x: x != ""]
                .unique()
                .tolist()
            )

            selected_industry = st.selectbox(
                "🏭 Search / Select Industry",
                industry_options,
                index=0,
                key="industry_explorer_selection"
            )

            # =================================================
            # DETERMINE PEER GROUP
            # =================================================

            # If a company is selected, automatically use
            # that company's industry.

            company_selected_industry = None

            if selected_peer_company != "None":

                selected_company_data = industry_data[
                    industry_data["Company"].astype(str)
                    == selected_peer_company
                ]

                if len(selected_company_data) > 0:

                    company_selected_industry = (
                        selected_company_data.iloc[0]["Industry"]
                    )

            # =================================================
            # COMPANY TAKES PRIORITY
            # =================================================

            if company_selected_industry is not None:

                comparison_industry = (
                    company_selected_industry
                )

                industry_companies = (
                    industry_data[
                        industry_data["Industry"]
                        == comparison_industry
                    ]
                    .copy()
                )

                st.info(
                    f"🏢 **{selected_peer_company}** belongs to "
                    f"**{comparison_industry}**. "
                    f"Showing its industry peers."
                )

            elif selected_industry == "All Industries":

                comparison_industry = "All Industries"

                industry_companies = (
                    industry_data.copy()
                )

            else:

                comparison_industry = selected_industry

                industry_companies = (
                    industry_data[
                        industry_data["Industry"]
                        == selected_industry
                    ]
                    .copy()
                )

            # =================================================
            # DISPLAY PEER GROUP
            # =================================================

            if comparison_industry == "All Industries":

                st.markdown(
                    "### 🌐 All Industries"
                )

                st.caption(
                    f"{len(industry_companies)} companies "
                    "within the current screened universe."
                )

            else:

                st.markdown(
                    f"### {comparison_industry}"
                )

                st.caption(
                    f"{len(industry_companies)} companies in this "
                    "industry within the current screened universe."
                )

            # =================================================
            # AVAILABLE METRICS
            # =================================================

            industry_metric_options = [
                metric
                for metric in field_aliases.keys()
                if field_aliases[metric]
                in industry_companies.columns
            ]

            # =================================================
            # DEFAULT INDUSTRY METRICS
            # =================================================

            if "industry_selected_metrics" not in st.session_state:

                st.session_state.industry_selected_metrics = []

            # Remove unavailable metrics

            st.session_state.industry_selected_metrics = [
                metric
                for metric
                in st.session_state.industry_selected_metrics
                if metric in industry_metric_options
            ]

            # =================================================
            # ADD METRIC
            # =================================================

            st.markdown("### 📊 Add Metric")

            available_metric_options = [
                metric
                for metric in industry_metric_options
                if metric
                not in st.session_state.industry_selected_metrics
            ]

            col1, col2 = st.columns([4, 1])

            with col1:

                if available_metric_options:

                    selected_industry_metric = st.selectbox(
                        "Metric",
                        ["None"] + available_metric_options,
                        key="industry_metric_to_add"
                    )

                else:

                    selected_industry_metric = None

                    st.info(
                        "All available metrics have been added."
                    )

            with col2:

                st.write("")
                st.write("")

                add_metric = st.button(
                    "➕ Add",
                    key="add_industry_metric"
                )

            if (
                add_metric
                and selected_industry_metric
                and selected_industry_metric != "None"
            ):

                if (
                    selected_industry_metric
                    not in st.session_state.industry_selected_metrics
                ):

                    st.session_state.industry_selected_metrics.append(
                        selected_industry_metric
                    )

                    st.rerun()

            # =================================================
            # CURRENT METRICS
            # =================================================

            st.caption("Selected metrics:")

            if st.session_state.industry_selected_metrics:

                metric_text = " • ".join(
                    st.session_state.industry_selected_metrics
                )

                st.info(metric_text)

            # =================================================
            # ADD STATISTIC
            # =================================================

            st.markdown("### 📈 Add Statistic")

            industry_statistic_options = [
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
                "vs Median"
            ]

            if "industry_selected_statistics" not in st.session_state:

                st.session_state.industry_selected_statistics = []

            available_statistic_options = [
                statistic
                for statistic in industry_statistic_options
                if statistic
                not in st.session_state.industry_selected_statistics
            ]

            col1, col2 = st.columns([4, 1])

            with col1:

                if available_statistic_options:

                    selected_industry_statistic = st.selectbox(
                        "Statistic",
                        ["None"] + available_statistic_options,
                        key="industry_statistic_to_add"
                    )

                else:

                    selected_industry_statistic = None

                    st.info(
                        "All statistics have been added."
                    )

            with col2:

                st.write("")
                st.write("")

                add_statistic = st.button(
                    "➕ Add",
                    key="add_industry_statistic"
                )

            if (
                add_statistic
                and selected_industry_statistic
                and selected_industry_statistic != "None"
            ):

                if (
                    selected_industry_statistic
                    not in st.session_state.industry_selected_statistics
                ):

                    # Mean and Median cannot be selected together
                    if selected_industry_statistic == "Mean":

                        st.session_state.industry_selected_statistics = [
                            statistic
                            for statistic
                            in st.session_state.industry_selected_statistics
                            if statistic != "Median"
                        ]

                    elif selected_industry_statistic == "Median":

                        st.session_state.industry_selected_statistics = [
                            statistic
                            for statistic
                            in st.session_state.industry_selected_statistics
                            if statistic != "Mean"
                        ]

                    st.session_state.industry_selected_statistics.append(
                        selected_industry_statistic
                    )

                    st.rerun()

            # =================================================
            # MAIN COMPARISON TABLE
            # =================================================

            st.markdown("### 👥 Companies")

            display_table = pd.DataFrame()

            display_table["Company"] = (
                industry_companies["Company"]
                .astype(str)
            )

            # =================================================
            # HELPER FOR COMPANY COMPARISON
            # =================================================

            higher_is_better = {
                "ROE",
                "ROCE",
                "Dividend Yield",
                "Div Yield",
                "Qtr Profit Var",
                "Qtr Sales Var",
                "Forecast EPS",
                "Forecast EPS Growth",
                "Forecast Revenue",
                "Forecast Revenue Growth"
            }

            lower_is_better = {
                "P/E",
                "P/B",
                "CMP / BV",
                "Forward P/E"
            }

            # =================================================
            # METRICS + STATISTICS
            # =================================================

            for metric in (
                st.session_state.industry_selected_metrics
            ):

                csv_field = field_aliases[metric]

                numeric_values = pd.to_numeric(
                    industry_companies[csv_field],
                    errors="coerce"
                )

                # Main metric

                display_table[metric] = (
                    numeric_values.values
                )

                valid_values = (
                    numeric_values.dropna()
                )

                if len(valid_values) == 0:
                    continue

                mean_value = valid_values.mean()
                median_value = valid_values.median()
                minimum_value = valid_values.min()
                maximum_value = valid_values.max()

                q25 = valid_values.quantile(0.25)
                q75 = valid_values.quantile(0.75)

                std_value = valid_values.std()

                iqr_value = (
                    q75 - q25
                )

                range_value = (
                    maximum_value
                    - minimum_value
                )

                ranks = numeric_values.rank(
                    method="min",
                    ascending=False
                )

                percentiles = (
                    numeric_values.rank(pct=True)
                    * 100
                )

                # =================================================
                # SELECTED STATISTICS
                # =================================================

                # Statistics that should be displayed above the table
                # instead of becoming columns.
                summary_statistics = {
                    "Mean",
                    "Median",
                    "Minimum",
                    "Maximum",
                    "25th Percentile",
                    "75th Percentile",
                    "Standard Deviation",
                    "IQR",
                    "Range",
                }

                for statistic in (
                    st.session_state.industry_selected_statistics
                ):

                    column_name = (
                        f"{metric} — {statistic}"
                    )

                    if statistic == "Rank":

                        display_table[column_name] = (
                            ranks.round().astype("Int64").values
                        )
                    elif statistic == "Percentile":

                        display_table[column_name] = (
                            percentiles.values
                        )

                    elif statistic == "Difference from Mean":

                        display_table[column_name] = (
                            numeric_values
                            - mean_value
                        )

                    elif statistic == "Difference from Median":

                        display_table[column_name] = (
                            numeric_values
                            - median_value
                        )

                    elif statistic == "vs Mean":

                        display_table[column_name] = (
                            numeric_values.apply(
                                lambda x:
                                "🟢 Above"
                                if x > mean_value
                                else (
                                    "🔴 Below"
                                    if x < mean_value
                                    else "⚪ Mean"
                                )
                                if pd.notna(x)
                                else "N/A"
                            )
                        )

                    elif statistic == "vs Median":

                        display_table[column_name] = (
                            numeric_values.apply(
                                lambda x:
                                "🟢 Above"
                                if x > median_value
                                else (
                                    "🔴 Below"
                                    if x < median_value
                                    else "⚪ Median"
                                )
                                if pd.notna(x)
                                else "N/A"
                            )
                        )
            # =================================================
            # HIGHLIGHT SELECTED COMPANY
            # =================================================

            if selected_peer_company != "None":

                display_table["Company"] = (
                    display_table["Company"].apply(
                        lambda x:
                        f"⭐ {x}"
                        if x == selected_peer_company
                        else x
                    )
                )

            # =================================================
            # COLOR MAIN PEER TABLE
            # =================================================

            def highlight_peer_table(column):

                styles = pd.Series(
                    "",
                    index=column.index
                )

                column_name = column.name

                # ---------------------------------------------
                # Metrics where HIGHER is better
                # ---------------------------------------------

                higher_metrics = {
                    "ROE",
                    "ROCE",
                    "Dividend Yield",
                    "Div Yield",
                    "Qtr Profit Var",
                    "Qtr Sales Var",
                    "Forecast EPS",
                    "Forecast EPS Growth",
                    "Forecast Revenue",
                    "Forecast Revenue Growth"
                }

                # ---------------------------------------------
                # Metrics where LOWER is better
                # ---------------------------------------------

                lower_metrics = {
                    "P/E",
                    "P/B",
                    "CMP / BV",
                    "Forward P/E"
                }
                
                # ---------------------------------------------
                # Don't color statistics columns
                # ---------------------------------------------

                if column_name in higher_metrics:

                    values = pd.to_numeric(
                        column,
                        errors="coerce"
                    )

                    valid_values = values.dropna()

                    if len(valid_values) > 0:

                        mean_value = valid_values.mean()

                        for index, value in values.items():

                            if pd.isna(value):
                                continue

                            if value > mean_value:

                                styles.loc[index] = (
                                    "color: green; "
                                    "font-weight: bold"
                                )

                            elif value < mean_value:

                                styles.loc[index] = (
                                    "color: red; "
                                    "font-weight: bold"
                                )

                elif column_name in lower_metrics:

                    values = pd.to_numeric(
                        column,
                        errors="coerce"
                    )

                    valid_values = values.dropna()

                    if len(valid_values) > 0:

                        mean_value = valid_values.mean()

                        for index, value in values.items():

                            if pd.isna(value):
                                continue

                            if value < mean_value:

                                styles.loc[index] = (
                                    "color: green; "
                                    "font-weight: bold"
                                )

                            elif value > mean_value:

                                styles.loc[index] = (
                                    "color: red; "
                                    "font-weight: bold"
                                )

                return styles


            # =================================================
            # SHOW SELECTED STATISTICS ABOVE TABLE
            # =================================================

            for statistic in (
                st.session_state.industry_selected_statistics
            ):

                if statistic not in summary_statistics:
                    continue

                statistic_values = []

                for metric in (
                    st.session_state.industry_selected_metrics
                ):

                    csv_field = field_aliases[metric]

                    numeric_values = pd.to_numeric(
                        industry_companies[csv_field],
                        errors="coerce"
                    ).dropna()

                    if len(numeric_values) == 0:
                        continue

                    if statistic == "Mean":
                        value = numeric_values.mean()

                    elif statistic == "Median":
                        value = numeric_values.median()

                    elif statistic == "Minimum":
                        value = numeric_values.min()

                    elif statistic == "Maximum":
                        value = numeric_values.max()

                    elif statistic == "25th Percentile":
                        value = numeric_values.quantile(0.25)

                    elif statistic == "75th Percentile":
                        value = numeric_values.quantile(0.75)

                    elif statistic == "Standard Deviation":
                        value = numeric_values.std()

                    elif statistic == "IQR":
                        value = (
                            numeric_values.quantile(0.75)
                            - numeric_values.quantile(0.25)
                        )

                    elif statistic == "Range":
                        value = (
                            numeric_values.max()
                            - numeric_values.min()
                        )

                    else:
                        continue

                    statistic_values.append(
                        f"**{metric}:** {value:.2f}"
                    )

                if statistic_values:

                    st.info(
                        f"**{statistic}**  •  "
                        + "  |  ".join(statistic_values)
                    )


            # =================================================
            # SHOW MAIN TABLE
            # =================================================

            # Show selected metric medians above the table
            if "Median" in st.session_state.industry_selected_statistics:

                median_values_text = []

                for metric in st.session_state.industry_selected_metrics:

                    csv_field = field_aliases[metric]

                    numeric_values = pd.to_numeric(
                        industry_companies[csv_field],
                        errors="coerce"
                    ).dropna()

                    if len(numeric_values) == 0:
                        continue

                    median_value = numeric_values.median()

                    median_values_text.append(
                        f"**{metric}:** {median_value:.2f}"
                    )


            styled_peer_table = (
                display_table.style
                .apply(
                    highlight_peer_table,
                    axis=0
                )
            )

            st.dataframe(
                styled_peer_table,
                use_container_width=True,
                hide_index=True
            )

            # =================================================
            # SELECTED COMPANY VS INDUSTRY
            # =================================================

            if selected_peer_company != "None":

                st.markdown(
                    f"### 🎯 {selected_peer_company} vs Industry"
                )

                selected_company_row = industry_data[
                    industry_data["Company"].astype(str)
                    == selected_peer_company
                ]

                if len(selected_company_row) > 0:

                    selected_company_row = (
                        selected_company_row.iloc[0]
                    )

                    comparison_rows = []

                    for metric in (
                        st.session_state.industry_selected_metrics
                    ):

                        csv_field = field_aliases[metric]

                        company_value = pd.to_numeric(
                            pd.Series(
                                [selected_company_row[csv_field]]
                            ),
                            errors="coerce"
                        ).iloc[0]

                        numeric_values = pd.to_numeric(
                            industry_companies[csv_field],
                            errors="coerce"
                        ).dropna()

                        if (
                            pd.isna(company_value)
                            or len(numeric_values) == 0
                        ):
                            continue

                        mean_value = (
                            numeric_values.mean()
                        )

                        median_value = (
                            numeric_values.median()
                        )

                        rank_series = (
                            numeric_values
                            .rank(
                                method="min",
                                ascending=False
                            )
                        )

                        matching_rank = rank_series[
                            numeric_values
                            == company_value
                        ]

                        company_rank = (
                            matching_rank.iloc[0]
                            if len(matching_rank) > 0
                            else None
                        )

                        percentile_series = (
                            numeric_values.rank(pct=True)
                            * 100
                        )

                        matching_percentile = (
                            percentile_series[
                                numeric_values
                                == company_value
                            ]
                        )

                        company_percentile = (
                            matching_percentile.iloc[0]
                            if len(matching_percentile) > 0
                            else None
                        )

                        comparison_rows.append({
                            "Metric": metric,
                            "Company Value": company_value,
                            "Industry Mean": mean_value,
                            "Industry Median": median_value,
                            "Rank": (
                                f"{int(company_rank)} / "
                                f"{len(numeric_values)}"
                                if company_rank is not None
                                else "N/A"
                            ),
                            "Percentile": (
                                f"{company_percentile:.1f}%"
                                if company_percentile is not None
                                else "N/A"
                            )
                        })

                    if comparison_rows:

                        comparison_df = pd.DataFrame(
                            comparison_rows
                        )

                        # =================================================
                        # COLOR COMPANY VALUE
                        # =================================================

                        def highlight_company_value(row):

                            styles = [
                                ""
                                for _ in row.index
                            ]

                            metric = row["Metric"]

                            company_value = (
                                row["Company Value"]
                            )

                            mean_value = (
                                row["Industry Mean"]
                            )

                            if pd.isna(company_value):
                                return styles

                            if metric in higher_is_better:

                                if company_value > mean_value:

                                    company_style = (
                                        "color: green; "
                                        "font-weight: bold"
                                    )

                                elif company_value < mean_value:

                                    company_style = (
                                        "color: red; "
                                        "font-weight: bold"
                                    )

                                else:

                                    company_style = (
                                        "font-weight: bold"
                                    )

                            elif metric in lower_is_better:

                                if company_value < mean_value:

                                    company_style = (
                                        "color: green; "
                                        "font-weight: bold"
                                    )

                                elif company_value > mean_value:

                                    company_style = (
                                        "color: red; "
                                        "font-weight: bold"
                                    )

                                else:

                                    company_style = (
                                        "font-weight: bold"
                                    )

                            else:

                                if company_value > mean_value:

                                    company_style = (
                                        "color: green; "
                                        "font-weight: bold"
                                    )

                                elif company_value < mean_value:

                                    company_style = (
                                        "color: red; "
                                        "font-weight: bold"
                                    )

                                else:

                                    company_style = (
                                        "font-weight: bold"
                                    )

                            styles[
                                row.index.get_loc(
                                    "Company Value"
                                )
                            ] = company_style

                            return styles

                        st.dataframe(
                            comparison_df.style.apply(
                                highlight_company_value,
                                axis=1
                            ),
                            use_container_width=True,
                            hide_index=True
                        )

                        st.caption(
                            "🟢 Green = company is favorable relative "
                            "to the industry mean. "
                            "🔴 Red = company is unfavorable relative "
                            "to the industry mean."
                        )
