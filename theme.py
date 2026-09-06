import streamlit as st


def apply_finance_theme():
    st.markdown(
        """
        <style>

        /* =========================
           GLOBAL BACKGROUND
        ========================= */

        .stApp {
            background:
                radial-gradient(
                    circle at 15% 15%,
                    rgba(0, 255, 170, 0.08),
                    transparent 25%
                ),
                radial-gradient(
                    circle at 85% 80%,
                    rgba(80, 120, 255, 0.10),
                    transparent 25%
                ),
                linear-gradient(
                    135deg,
                    #05070d 0%,
                    #080b12 50%,
                    #05070d 100%
                );

            color: #e8eef7;
        }


        /* =========================
           SUBTLE FINANCIAL GRID
        ========================= */

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;

            background-image:
                linear-gradient(
                    rgba(255,255,255,0.025) 1px,
                    transparent 1px
                ),
                linear-gradient(
                    90deg,
                    rgba(255,255,255,0.025) 1px,
                    transparent 1px
                );

            background-size: 45px 45px;

            pointer-events: none;
            z-index: 0;
        }


        /* =========================
           MAIN CONTENT
        ========================= */

        .block-container {
            position: relative;
            z-index: 1;

            max-width: 1400px;

            padding-top: 2rem;
            padding-bottom: 3rem;
        }


        /* =========================
           HEADINGS
        ========================= */

        h1 {
            font-weight: 800 !important;
            letter-spacing: -1px;
        }

        h2, h3 {
            font-weight: 700 !important;
        }


        /* =========================
           GLASS CARDS
        ========================= */

        div[data-testid="stMetric"],
        div[data-testid="stExpander"],
        div[data-testid="stDataFrame"] {

            background: rgba(255,255,255,0.035);

            border: 1px solid rgba(255,255,255,0.07);

            border-radius: 16px;

            backdrop-filter: blur(12px);

            box-shadow:
                0 8px 30px rgba(0,0,0,0.25);
        }


        /* =========================
           METRICS
        ========================= */

        div[data-testid="stMetric"] {
            padding: 18px;
        }

        div[data-testid="stMetricLabel"] {
            color: #8d9aae !important;
        }

        div[data-testid="stMetricValue"] {
            color: #f2f6fc !important;
            font-weight: 750 !important;
        }


        /* =========================
           INPUTS
        ========================= */

        div[data-baseweb="input"],
        div[data-baseweb="select"] {

            background: rgba(255,255,255,0.04);

            border-radius: 10px;
        }


        /* =========================
           BUTTONS
        ========================= */

        .stButton > button {

            border-radius: 10px;

            border: 1px solid rgba(0,255,170,0.25);

            background: rgba(0,255,170,0.08);

            color: #7fffd4;

            font-weight: 600;

            transition: 0.2s ease;
        }

        .stButton > button:hover {

            border-color: rgba(0,255,170,0.6);

            background: rgba(0,255,170,0.14);

            transform: translateY(-1px);
        }


        /* =========================
           DATAFRAME
        ========================= */

        div[data-testid="stDataFrame"] {

            overflow: hidden;
        }


        /* =========================
           SIDEBAR
        ========================= */

        section[data-testid="stSidebar"] {

            background:
                linear-gradient(
                    180deg,
                    #070a11,
                    #05070d
                );

            border-right: 1px solid rgba(255,255,255,0.06);
        }


        /* =========================
           FINANCE STATUS COLORS
        ========================= */

        .profit {
            color: #00e6a0;
        }

        .loss {
            color: #ff5c7a;
        }


        /* =========================
           MOBILE
        ========================= */

        @media (max-width: 768px) {

            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
                padding-top: 1rem;
            }

            h1 {
                font-size: 1.8rem !important;
            }

            h2 {
                font-size: 1.4rem !important;
            }

            h3 {
                font-size: 1.15rem !important;
            }

            div[data-testid="stMetric"] {
                padding: 12px;
            }

            div[data-testid="stDataFrame"] {
                font-size: 12px;
            }

        }

        </style>
        """,
        unsafe_allow_html=True
    )
