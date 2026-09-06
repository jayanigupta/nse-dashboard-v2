import streamlit as st


def apply_finance_theme():
    st.markdown(
        """
        <style>

        /* =========================================================
           GLOBAL APP
        ========================================================= */

        .stApp {
            background:
                radial-gradient(
                    circle at 10% 10%,
                    rgba(0, 255, 170, 0.10),
                    transparent 22%
                ),
                radial-gradient(
                    circle at 90% 85%,
                    rgba(90, 100, 255, 0.12),
                    transparent 25%
                ),
                radial-gradient(
                    circle at 70% 20%,
                    rgba(0, 200, 255, 0.055),
                    transparent 20%
                ),
                linear-gradient(
                    135deg,
                    #04060b 0%,
                    #070a12 45%,
                    #05070d 100%
                );

            color: #e8eef7;

            overflow-x: hidden;
        }


        /* =========================================================
           FLOATING BUBBLES
           Lightweight CSS-only animation
           ========================================================= */

        .stApp::after {
            content: "";

            position: fixed;

            width: 420px;
            height: 420px;

            left: -120px;
            top: 15%;

            border-radius: 50%;

            background:
                radial-gradient(
                    circle at 35% 30%,
                    rgba(0,255,190,0.16),
                    rgba(0,255,190,0.035) 45%,
                    transparent 70%
                );

            filter: blur(2px);

            pointer-events: none;

            z-index: 0;

            animation: floatOrb1 18s ease-in-out infinite alternate;
        }


        .stApp::before {
            content: "";

            position: fixed;

            width: 500px;
            height: 500px;

            right: -180px;
            bottom: -120px;

            border-radius: 50%;

            background:
                radial-gradient(
                    circle at 40% 35%,
                    rgba(80,120,255,0.17),
                    rgba(80,120,255,0.035) 45%,
                    transparent 70%
                );

            filter: blur(4px);

            pointer-events: none;

            z-index: 0;

            animation: floatOrb2 22s ease-in-out infinite alternate;
        }


        @keyframes floatOrb1 {

            0% {
                transform:
                    translate3d(0, 0, 0)
                    scale(1);
            }

            50% {
                transform:
                    translate3d(90px, -50px, 0)
                    scale(1.08);
            }

            100% {
                transform:
                    translate3d(40px, 80px, 0)
                    scale(0.94);
            }
        }


        @keyframes floatOrb2 {

            0% {
                transform:
                    translate3d(0, 0, 0)
                    scale(1);
            }

            50% {
                transform:
                    translate3d(-100px, -60px, 0)
                    scale(1.12);
            }

            100% {
                transform:
                    translate3d(-30px, 70px, 0)
                    scale(0.95);
            }
        }


        /* =========================================================
           FINANCIAL GRID
           ========================================================= */

        .stApp {
            background-image:
                linear-gradient(
                    rgba(255,255,255,0.018) 1px,
                    transparent 1px
                ),
                linear-gradient(
                    90deg,
                    rgba(255,255,255,0.018) 1px,
                    transparent 1px
                ),
                radial-gradient(
                    circle at 50% 50%,
                    transparent 0%,
                    rgba(0,0,0,0.15) 100%
                );

            background-size:
                48px 48px,
                48px 48px,
                100% 100%;
        }


        /* =========================================================
           MOVING LIGHT
           ========================================================= */

        div[data-testid="stAppViewContainer"]::before {

            content: "";

            position: fixed;

            width: 650px;
            height: 650px;

            left: 35%;
            top: 25%;

            border-radius: 50%;

            background:
                radial-gradient(
                    circle,
                    rgba(0,255,180,0.035),
                    transparent 65%
                );

            filter: blur(30px);

            pointer-events: none;

            z-index: 0;

            animation: ambientGlow 25s ease-in-out infinite alternate;
        }


        @keyframes ambientGlow {

            0% {
                transform:
                    translate(-20%, -10%);
            }

            50% {
                transform:
                    translate(15%, 10%);
            }

            100% {
                transform:
                    translate(-5%, 20%);
            }
        }


        /* =========================================================
           CONTENT
           ========================================================= */

        .block-container {

            position: relative;

            z-index: 2;

            max-width: 1400px;

            padding-top: 2rem;
            padding-bottom: 3rem;
        }


        /* =========================================================
           HEADINGS
           ========================================================= */

        h1 {

            font-weight: 800 !important;

            letter-spacing: -1.5px;

            background:
                linear-gradient(
                    110deg,
                    #ffffff 20%,
                    #9ffff0 55%,
                    #aab8ff 90%
                );

            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;

            background-size: 200% auto;

            animation: titleShimmer 8s ease-in-out infinite;
        }


        @keyframes titleShimmer {

            0%, 100% {
                background-position: 0% center;
            }

            50% {
                background-position: 100% center;
            }
        }


        h2, h3 {
            font-weight: 700 !important;
        }


        /* =========================================================
           GLASS CARDS
           ========================================================= */

        div[data-testid="stMetric"],
        div[data-testid="stExpander"],
        div[data-testid="stDataFrame"] {

            background:
                linear-gradient(
                    135deg,
                    rgba(255,255,255,0.055),
                    rgba(255,255,255,0.018)
                );

            border:

                1px solid
                rgba(255,255,255,0.075);

            border-radius: 18px;

            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);

            box-shadow:

                0 12px 40px
                rgba(0,0,0,0.25),

                inset 0 1px 0
                rgba(255,255,255,0.045);

            transition:
                transform 0.25s ease,
                border-color 0.25s ease,
                box-shadow 0.25s ease;
        }


        /* Subtle hover */

        div[data-testid="stMetric"]:hover {

            transform: translateY(-3px);

            border-color:
                rgba(0,255,180,0.18);

            box-shadow:

                0 16px 45px
                rgba(0,0,0,0.30),

                0 0 25px
                rgba(0,255,180,0.035);
        }


        /* =========================================================
           METRICS
           ========================================================= */

        div[data-testid="stMetric"] {

            padding: 18px;

            position: relative;

            overflow: hidden;
        }


        /* Tiny shine across metric cards */

        div[data-testid="stMetric"]::after {

            content: "";

            position: absolute;

            width: 80px;
            height: 180%;

            top: -40%;
            left: -100px;

            background:
                linear-gradient(
                    90deg,
                    transparent,
                    rgba(255,255,255,0.045),
                    transparent
                );

            transform: rotate(20deg);

            animation: cardShine 9s ease-in-out infinite;
        }


        @keyframes cardShine {

            0%, 70% {
                left: -120px;
            }

            100% {
                left: 120%;
            }
        }


        div[data-testid="stMetricLabel"] {

            color: #8d9aae !important;

            font-size: 0.85rem !important;
        }


        div[data-testid="stMetricValue"] {

            color: #f2f6fc !important;

            font-weight: 750 !important;
        }


        /* =========================================================
           INPUTS
           ========================================================= */

        div[data-baseweb="input"],
        div[data-baseweb="select"] {

            background:
                rgba(255,255,255,0.035);

            border-radius: 12px;

            border-color:
                rgba(255,255,255,0.06);
        }


        /* =========================================================
           BUTTONS
           ========================================================= */

        .stButton > button {

            border-radius: 12px;

            border:
                1px solid
                rgba(0,255,170,0.22);

            background:
                linear-gradient(
                    135deg,
                    rgba(0,255,170,0.09),
                    rgba(0,180,255,0.055)
                );

            color: #86ffe0;

            font-weight: 600;

            box-shadow:
                0 4px 18px
                rgba(0,255,170,0.04);

            transition:
                all 0.22s ease;
        }


        .stButton > button:hover {

            border-color:
                rgba(0,255,170,0.55);

            background:
                linear-gradient(
                    135deg,
                    rgba(0,255,170,0.16),
                    rgba(0,180,255,0.10)
                );

            color: #ffffff;

            transform:
                translateY(-2px);

            box-shadow:
                0 8px 25px
                rgba(0,255,170,0.08);
        }


        /* =========================================================
           DATAFRAME
           ========================================================= */

        div[data-testid="stDataFrame"] {

            overflow: hidden;

            border-radius: 18px;
        }


        /* =========================================================
           SIDEBAR
           ========================================================= */

        section[data-testid="stSidebar"] {

            background:
                linear-gradient(
                    180deg,
                    rgba(7,10,17,0.96),
                    rgba(4,6,11,0.98)
                );

            border-right:
                1px solid
                rgba(255,255,255,0.06);

            backdrop-filter:
                blur(20px);
        }


        /* =========================================================
           FINANCE STATUS
           ========================================================= */

        .profit {

            color: #00e6a0;

            text-shadow:
                0 0 12px
                rgba(0,230,160,0.25);
        }


        .loss {

            color: #ff5c7a;

            text-shadow:
                0 0 12px
                rgba(255,92,122,0.20);
        }


        /* =========================================================
           SCROLLBAR
           ========================================================= */

        ::-webkit-scrollbar {

            width: 7px;
            height: 7px;
        }


        ::-webkit-scrollbar-track {

            background:
                rgba(255,255,255,0.015);
        }


        ::-webkit-scrollbar-thumb {

            background:
                rgba(255,255,255,0.12);

            border-radius: 20px;
        }


        ::-webkit-scrollbar-thumb:hover {

            background:
                rgba(0,255,170,0.25);
        }


        /* =========================================================
           MOBILE
           ========================================================= */

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


            /* Reduce animation footprint on phones */

            .stApp::after {

                width: 280px;
                height: 280px;
            }


            .stApp::before {

                width: 320px;
                height: 320px;
            }

        }


        /* =========================================================
           ACCESSIBILITY / PERFORMANCE
           ========================================================= */

        @media (prefers-reduced-motion: reduce) {

            *,
            *::before,
            *::after {

                animation-duration: 0.01ms !important;

                animation-iteration-count: 1 !important;

                scroll-behavior: auto !important;
            }
        }

        </style>
        """,
        unsafe_allow_html=True
    )
