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


# =========================
# LOAD INDUSTRY DATA
# =========================

@st.cache_data
def load_industry_data():
    return pd.read_csv("nifty500.csv")


industry_df = load_industry_data()

industry_df.columns = (
    industry_df.columns
    .str.strip()
    .str.replace(r"\s+", " ", regex=True)
)


# =========================
# CLEAN COMPANY NAMES
# =========================

def clean_company_name(name):

    if pd.isna(name):
        return ""

    name = str(name).upper().strip()

    for suffix in [
        " LIMITED",
        " LTD.",
        " LTD",
        " LIMITED.",
        " PVT. LTD.",
        " PVT LTD",
        " PRIVATE LIMITED"
    ]:

        if name.endswith(suffix):
            name = name[:-len(suffix)]

    return name.strip()


df["_CompanyMatch"] = df["Company"].apply(
    clean_company_name
)

industry_df["_CompanyMatch"] = industry_df["Company Name"].apply(
    clean_company_name
)


# =========================
# ADD INDUSTRY
# =========================

industry_mapping = (
    industry_df[
        ["_CompanyMatch", "Symbol", "Industry"]
    ]
    .drop_duplicates("_CompanyMatch")
)

df = df.merge(
    industry_mapping,
    on="_CompanyMatch",
    how="left"
)

df.drop(
    columns=["_CompanyMatch"],
    inplace=True
)

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

if "peer_selected_metrics" not in st.session_state:
    st.session_state.peer_selected_metrics = []

if "peer_selected_stats" not in st.session_state:
    st.session_state.peer_selected_stats = ["Value"]


# =========================
# FILTER BUILDER
# =========================

st.subheader("🔎 Build Your Screen")

col1, col2, col3, col4 = st.columns(
    [3, 1.5, 2, 1.2]
)


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

    st.session_state.filters = []
    st.session_state.selected_field = "P/E"
    st.session_state.screen_result = None

    st.session_state.peer_selected_metrics = []
    st.session_state.peer_selected_stats = ["Value"]

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


# =========================================================
# INDUSTRY EXPLORER
# =========================================================

if st.session_state.screen_result is not None:

    st.divider()

    st.subheader("🏭 Industry Explorer")

    st.caption(
        "Select an industry and company, then add metrics and statistics "
        "to compare the company with its industry peers."
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
            industry_data["Industry"].notna()
            & (industry_data["Industry"] != "")
            & (industry_data["Industry"].str.lower() != "nan")
        ].copy()

        if len(industry_data) == 0:

            st.warning(
                "No industry information is available."
            )

        else:

            # =====================================================
            # SELECT INDUSTRY
            # =====================================================

            industries = sorted(
                industry_data["Industry"]
                .unique()
                .tolist()
            )

            selected_industry = st.selectbox(
                "🏭 Select Industry",
                industries,
                key="industry_explorer"
            )

            # ALL companies in selected industry
            industry_companies = (
                industry_data[
                    industry_data["Industry"]
                    == selected_industry
                ]
                .copy()
            )

            st.markdown(
                f"### {selected_industry}"
            )

            st.caption(
                f"{len(industry_companies)} companies in this industry "
                f"within the current screened universe."
            )

            # =====================================================
            # SELECT COMPANY
            # =====================================================

            company_options = (
                industry_companies["Company"]
                .dropna()
                .astype(str)
                .sort_values()
                .unique()
                .tolist()
            )

            selected_peer_company = st.selectbox(
                "🎯 Select Company",
                ["None"] + company_options,
                key="industry_company_selection"
            )

            # =====================================================
            # ADD METRIC
            # =====================================================

            st.markdown("### 📊 Add Metric")

            industry_metric_options = [
                metric
                for metric in field_aliases.keys()
                if field_aliases[metric] in industry_companies.columns
            ]

            col1, col2 = st.columns([4, 1])

            with col1:

                selected_industry_metric = st.selectbox(
                    "Metric",
                    industry_metric_options,
                    key="industry_metric_to_add"
                )

            with col2:

                st.write("")
                st.write("")

                add_metric = st.button(
                    "➕ Add",
                    key="add_industry_metric"
                )

            if "industry_selected_metrics" not in st.session_state:
                st.session_state.industry_selected_metrics = []

            if add_metric:

                if (
                    selected_industry_metric
                    not in st.session_state.industry_selected_metrics
                ):

                    st.session_state.industry_selected_metrics.append(
                        selected_industry_metric
                    )

            # =====================================================
            # CURRENT METRICS
            # =====================================================

            if st.session_state.industry_selected_metrics:

                st.caption("Added metrics:")

                metric_text = " • ".join(
                    st.session_state.industry_selected_metrics
                )

                st.info(metric_text)

            # =====================================================
            # ADD STATISTIC
            # =====================================================

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

            col1, col2 = st.columns([4, 1])

            with col1:

                selected_industry_statistic = st.selectbox(
                    "Statistic",
                    industry_statistic_options,
                    key="industry_statistic_to_add"
                )

            with col2:

                st.write("")
                st.write("")

                add_statistic = st.button(
                    "➕ Add",
                    key="add_industry_statistic"
                )

            if "industry_selected_statistics" not in st.session_state:
                st.session_state.industry_selected_statistics = []

            if add_statistic:

                if (
                    selected_industry_statistic
                    not in st.session_state.industry_selected_statistics
                ):

                    st.session_state.industry_selected_statistics.append(
                        selected_industry_statistic
                    )

            # =====================================================
            # CURRENT STATISTICS
            # =====================================================

            if st.session_state.industry_selected_statistics:

                st.caption("Added statistics:")

                statistic_text = " • ".join(
                    st.session_state.industry_selected_statistics
                )

                st.info(statistic_text)

            # =====================================================
            # MAIN INDUSTRY TABLE
            # =====================================================

            if st.session_state.industry_selected_metrics:

                st.markdown("### 👥 Industry Companies")

                display_table = pd.DataFrame()

                display_table["Company"] = (
                    industry_companies["Company"]
                    .astype(str)
                )

                # Highlight selected company
                if selected_peer_company != "None":

                    display_table["Company"] = display_table[
                        "Company"
                    ].apply(
                        lambda x:
                        f"⭐ {x}"
                        if x == selected_peer_company
                        else x
                    )

                # -------------------------------------------------
                # EACH SELECTED METRIC
                # -------------------------------------------------

                for metric in st.session_state.industry_selected_metrics:

                    csv_field = field_aliases[metric]

                    numeric_values = pd.to_numeric(
                        industry_companies[csv_field],
                        errors="coerce"
                    )

                    display_table[metric] = numeric_values.values

                    # -------------------------------------------------
                    # STATISTICS FOR THIS METRIC
                    # -------------------------------------------------

                    valid_values = numeric_values.dropna()

                    if len(valid_values) == 0:
                        continue

                    mean_value = valid_values.mean()
                    median_value = valid_values.median()
                    minimum_value = valid_values.min()
                    maximum_value = valid_values.max()

                    q25 = valid_values.quantile(0.25)
                    q75 = valid_values.quantile(0.75)

                    std_value = valid_values.std()

                    iqr_value = q75 - q25

                    range_value = (
                        maximum_value
                        - minimum_value
                    )

                    # Rank
                    ranks = numeric_values.rank(
                        method="min",
                        ascending=False
                    )

                    # Percentile
                    percentiles = numeric_values.rank(
                        pct=True
                    ) * 100

                    # -------------------------------------------------
                    # ADD SELECTED STATISTICS
                    # -------------------------------------------------

                    for statistic in (
                        st.session_state
                        .industry_selected_statistics
                    ):

                        column_name = (
                            f"{metric} — {statistic}"
                        )

                        if statistic == "Mean":

                            display_table[column_name] = (
                                mean_value
                            )

                        elif statistic == "Median":

                            display_table[column_name] = (
                                median_value
                            )

                        elif statistic == "Minimum":

                            display_table[column_name] = (
                                minimum_value
                            )

                        elif statistic == "Maximum":

                            display_table[column_name] = (
                                maximum_value
                            )

                        elif statistic == "25th Percentile":

                            display_table[column_name] = (
                                q25
                            )

                        elif statistic == "75th Percentile":

                            display_table[column_name] = (
                                q75
                            )

                        elif statistic == "Standard Deviation":

                            display_table[column_name] = (
                                std_value
                            )

                        elif statistic == "IQR":

                            display_table[column_name] = (
                                iqr_value
                            )

                        elif statistic == "Range":

                            display_table[column_name] = (
                                range_value
                            )

                        elif statistic == "Rank":

                            display_table[column_name] = (
                                ranks.values
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

                # -------------------------------------------------
                # SHOW TABLE
                # -------------------------------------------------

                st.dataframe(
                    display_table,
                    use_container_width=True,
                    hide_index=True
                )

                # =================================================
                # SELECTED COMPANY COMPARISON
                # =================================================

                if selected_peer_company != "None":

                    st.markdown(
                        f"### 🎯 {selected_peer_company} vs Industry"
                    )

                    selected_company_row = industry_companies[
                        industry_companies["Company"].astype(str)
                        == selected_peer_company
                    ]

                    if len(selected_company_row) > 0:

                        selected_company_row = (
                            selected_company_row.iloc[0]
                        )

                        comparison_rows = []

                        for metric in (
                            st.session_state
                            .industry_selected_metrics
                        ):

                            csv_field = field_aliases[metric]

                            value = pd.to_numeric(
                                pd.Series(
                                    [selected_company_row[csv_field]]
                                ),
                                errors="coerce"
                            ).iloc[0]

                            numeric_values = pd.to_numeric(
                                industry_companies[csv_field],
                                errors="coerce"
                            ).dropna()

                            if pd.isna(value) or len(numeric_values) == 0:
                                continue

                            mean_value = numeric_values.mean()
                            median_value = numeric_values.median()

                            rank = (
                                numeric_values
                                .rank(
                                    method="min",
                                    ascending=False
                                )
                            )

                            company_rank = (
                                rank[
                                    numeric_values
                                    == value
                                ]
                                .iloc[0]
                            )

                            percentile = (
                                numeric_values
                                .rank(pct=True)
                                [
                                    numeric_values
                                    == value
                                ]
                                .iloc[0]
                                * 100
                            )

                            comparison_rows.append({
                                "Metric": metric,
                                "Company Value": value,
                                "Industry Mean": mean_value,
                                "Industry Median": median_value,
                                "Rank": f"{int(company_rank)} / {len(numeric_values)}",
                                "Percentile": f"{percentile:.1f}%"
                            })

                        if comparison_rows:

                            st.dataframe(
                                pd.DataFrame(comparison_rows),
                                use_container_width=True,
                                hide_index=True
                            )

            # =====================================================
            # INDUSTRY SUMMARY BOX
            # =====================================================

            if st.session_state.industry_selected_metrics:

                st.markdown("### 📦 Industry Statistics")

                summary_rows = []

                for metric in (
                    st.session_state.industry_selected_metrics
                ):

                    csv_field = field_aliases[metric]

                    values = pd.to_numeric(
                        industry_companies[csv_field],
                        errors="coerce"
                    ).dropna()

                    if len(values) == 0:
                        continue

                    summary = {
                        "Metric": metric,
                        "Companies": len(values)
                    }

                    if "Mean" in st.session_state.industry_selected_statistics:
                        summary["Mean"] = values.mean()

                    if "Median" in st.session_state.industry_selected_statistics:
                        summary["Median"] = values.median()

                    if "Minimum" in st.session_state.industry_selected_statistics:
                        summary["Minimum"] = values.min()

                    if "Maximum" in st.session_state.industry_selected_statistics:
                        summary["Maximum"] = values.max()

                    if "25th Percentile" in st.session_state.industry_selected_statistics:
                        summary["25th Percentile"] = values.quantile(0.25)

                    if "75th Percentile" in st.session_state.industry_selected_statistics:
                        summary["75th Percentile"] = values.quantile(0.75)

                    if "Standard Deviation" in st.session_state.industry_selected_statistics:
                        summary["Standard Deviation"] = values.std()

                    if "IQR" in st.session_state.industry_selected_statistics:
                        summary["IQR"] = (
                            values.quantile(0.75)
                            - values.quantile(0.25)
                        )

                    if "Range" in st.session_state.industry_selected_statistics:
                        summary["Range"] = (
                            values.max()
                            - values.min()
                        )

                    summary_rows.append(summary)

                if summary_rows:

                    st.dataframe(
                        pd.DataFrame(summary_rows),
                        use_container_width=True,
                        hide_index=True
                    )


# =========================================================
# DAILY STATISTICS
# TEMPORARILY COMMENTED OUT
# =========================================================

"""
if st.session_state.screen_result is not None:

    result = (
        st.session_state.screen_result
        .copy()
    )

    st.divider()

    st.subheader(
        "📊 Daily Statistics"
    )

    st.caption(
        "Compare multiple financial metrics across the screened companies."
    )


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

        if numeric_values.notna().sum() > 0:

            numeric_metrics[column] = column


    metric_names = {

        "P/E": "P/E",

        "CMP / BV": "P/B",

        "ROCE %": "ROCE",

        "ROE 10Yr %": "ROE",

        "Div Yld %": "Dividend Yield",

        "Mar Cap Rs.Cr.": "Market Cap",

        "CMP Rs.": "Current Market Price",

        "Qtr Sales Var %":
            "Quarterly Sales Growth",

        "Qtr Profit Var %":
            "Quarterly Profit Growth",

        "Ind PBV":
            "Industry PBV"
    }


    display_metrics = {
        metric_names.get(
            column,
            column
        ): column

        for column in numeric_metrics
    }


    st.markdown(
        "### 📌 Metrics"
    )

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

        st.markdown(
            "### 🔘 What do you want to display?"
        )

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


        button_cols = st.columns(4)


        for i, option in enumerate(
            statistic_options
        ):

            with button_cols[
                i % 4
            ]:

                is_selected = (
                    option
                    in st.session_state.selected_daily_stats
                )

                button_text = (
                    "✓ "
                    if is_selected
                    else ""
                ) + option


                if st.button(
                    button_text,
                    key=f"daily_stat_button_{i}",
                    use_container_width=True
                ):

                    if option in (
                        st.session_state.selected_daily_stats
                    ):

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


        comparison_table = pd.DataFrame({
            "Company": result["Company"]
        })


        for metric in selected_metrics:

            column = display_metrics[metric]

            values = pd.to_numeric(
                result[column],
                errors="coerce"
            )

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


            if "Value" in selected_stats:

                comparison_table[
                    metric
                ] = values.round(2)


            if "Mean" in selected_stats:

                comparison_table[
                    f"{metric} Mean"
                ] = round(
                    mean_value,
                    2
                )


            if "Median" in selected_stats:

                comparison_table[
                    f"{metric} Median"
                ] = round(
                    median_value,
                    2
                )


            if "Minimum" in selected_stats:

                comparison_table[
                    f"{metric} Min"
                ] = round(
                    minimum,
                    2
                )


            if "Maximum" in selected_stats:

                comparison_table[
                    f"{metric} Max"
                ] = round(
                    maximum,
                    2
                )


            if "25th Percentile" in selected_stats:

                comparison_table[
                    f"{metric} Q1"
                ] = round(
                    q1,
                    2
                )


            if "75th Percentile" in selected_stats:

                comparison_table[
                    f"{metric} Q3"
                ] = round(
                    q3,
                    2
                )


            if "Standard Deviation" in selected_stats:

                comparison_table[
                    f"{metric} Std Dev"
                ] = round(
                    std_dev,
                    2
                )


            if "IQR" in selected_stats:

                comparison_table[
                    f"{metric} IQR"
                ] = round(
                    iqr,
                    2
                )


            if "Range" in selected_stats:

                comparison_table[
                    f"{metric} Range"
                ] = round(
                    value_range,
                    2
                )


            if "Rank" in selected_stats:

                comparison_table[
                    f"{metric} Rank"
                ] = (
                    values.rank(
                        ascending=False,
                        method="min"
                    )
                )


            if "Percentile" in selected_stats:

                comparison_table[
                    f"{metric} Percentile"
                ] = (
                    values.rank(
                        pct=True,
                        method="average"
                    )
                    * 100
                ).round(1)


            if "Difference from Mean" in selected_stats:

                comparison_table[
                    f"{metric} Δ Mean"
                ] = (
                    values
                    - mean_value
                ).round(2)


            if "Difference from Median" in selected_stats:

                comparison_table[
                    f"{metric} Δ Median"
                ] = (
                    values
                    - median_value
                ).round(2)


            if "vs Mean" in selected_stats:

                comparison_table[
                    f"{metric} vs Mean"
                ] = values.apply(
                    lambda x:
                    "🟢 Above"
                    if pd.notna(x)
                    and x > mean_value

                    else (
                        "🔴 Below"
                        if pd.notna(x)
                        and x < mean_value

                        else (
                            "⚪ Mean"
                            if pd.notna(x)
                            else "—"
                        )
                    )
                )


            if "vs Median" in selected_stats:

                comparison_table[
                    f"{metric} vs Median"
                ] = values.apply(
                    lambda x:
                    "🟢 Above"
                    if pd.notna(x)
                    and x > median_value

                    else (
                        "🔴 Below"
                        if pd.notna(x)
                        and x < median_value

                        else (
                            "⚪ Median"
                            if pd.notna(x)
                            else "—"
                        )
                    )
                )


        st.markdown(
            "### 📋 Company Comparison"
        )

        st.dataframe(
            comparison_table,
            use_container_width=True,
            hide_index=True
        )


        st.markdown(
            "### 📈 Daily Summary"
        )

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

                "Mean": round(
                    values.mean(),
                    2
                ),

                "Median": round(
                    values.median(),
                    2
                ),

                "Min": round(
                    values.min(),
                    2
                ),

                "25th Percentile": round(
                    values.quantile(0.25),
                    2
                ),

                "75th Percentile": round(
                    values.quantile(0.75),
                    2
                ),

                "Max": round(
                    values.max(),
                    2
                ),

                "Std Dev": round(
                    values.std(),
                    2
                ),

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
"""


# =========================================================
# RATIOS
# =========================================================

st.divider()

st.subheader("📐 Ratios")

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


gallery_map = {
    "Price to Earning": "P/E",
    "Price to book value": "P/B",
    "Return on equity": "ROE",
    "Return on capital employed": "ROCE",
    "Dividend yield": "Dividend Yield",
}


cols = st.columns(4)


for i, metric in enumerate(
    ratios_metrics
):

    with cols[
        i % 4
    ]:

        if st.button(
            metric,
            key=f"ratio_{i}",
            use_container_width=True
        ):

            if metric in gallery_map:

                st.session_state.selected_field = (
                    gallery_map[metric]
                )

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
