import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

st.set_page_config(page_title="Stock Chart", page_icon="📈", layout="wide")

st.title("📈 Stock Chart Viewer")
st.caption("View candlestick charts for any NSE stock")

col1, col2 = st.columns([2, 1])

with col1:
    symbol = st.text_input("Enter Stock Symbol (e.g. RELIANCE, TCS, INFY)", value="RELIANCE")
with col2:
    period = st.radio("Period", ["1mo", "3mo", "6mo", "1y"], horizontal=True)

if symbol:
    ticker = yf.Ticker(f"{symbol.upper()}.NS")
    hist = ticker.history(period=period)

    if hist.empty:
        st.warning(f"No data found for {symbol.upper()} — check the symbol and try again!")
    else:
        fig = go.Figure(data=[go.Candlestick(
            x=hist.index,
            open=hist["Open"],
            high=hist["High"],
            low=hist["Low"],
            close=hist["Close"],
            increasing_line_color="#00C897",
            decreasing_line_color="#FF6B6B"
        )])

        fig.update_layout(
            title=f"{symbol.upper()} — {period} Candlestick Chart",
            xaxis_title="Date",
            yaxis_title="Price (₹)",
            plot_bgcolor="#0E1117",
            paper_bgcolor="#0E1117",
            font_color="#FAFAFA",
            xaxis_rangeslider_visible=False,
            height=550
        )

        st.plotly_chart(fig, use_container_width=True)

        # ── Quick stats ──────────────────────────────────────
        st.divider()
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Current Price", f"₹{hist['Close'].iloc[-1]:.2f}")
        col_b.metric("Period High", f"₹{hist['High'].max():.2f}")
        col_c.metric("Period Low", f"₹{hist['Low'].min():.2f}")
        col_d.metric("Avg Volume", f"{hist['Volume'].mean():,.0f}")
