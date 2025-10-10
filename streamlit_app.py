# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

st.set_page_config(page_title="AlphaLayer", page_icon="📊", layout="wide")
st.title("💹 AlphaLayer — Augmented Market Insights")
st.markdown("Data-driven, rule-based Buy / Sell / Hold signals. (PoC)")

# ---- helper: force a close series to 1D numeric pd.Series ----
def to_1d_series(df, col="Close"):
    """
    Ensure df[col] is a 1D pandas Series of floats indexed by df.index.
    Handles cases where df[col] is a DataFrame (n,1) or ndarray (n,1).
    """
    if col not in df.columns:
        raise KeyError(f"Column '{col}' not in DataFrame")

    series_like = df[col]

    # If it's a DataFrame with single column, take the first column
    if isinstance(series_like, pd.DataFrame):
        # pick first column
        series_like = series_like.iloc[:, 0]

    # If numpy array, ravel it
    if isinstance(series_like, np.ndarray):
        series_like = series_like.ravel()
        series_like = pd.Series(series_like, index=df.index)

    # Now coerce to numeric and preserve index
    series_like = pd.to_numeric(series_like, errors="coerce")
    series_like.index = df.index

    # Forward/backward fill small gaps (so ta functions don't fail)
    series_like = series_like.fillna(method="ffill").fillna(method="bfill")

    return series_like.astype(float)

# ---- analysis function ----
def analyze_ticker(ticker, min_days=50):
    try:
        # download recent 1 year of daily data (you can increase period)
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty or len(df) < 10:
            return {"Ticker": ticker, "Action": "No Data", "Price": "N/A", "RSI": "N/A", "MA50": "N/A", "Potential Gain %": "N/A", "Link": ""}

        # Ensure Close is 1D numeric series
        close_s = to_1d_series(df, "Close")

        # If after coercion there are still too many NaNs, bail
        if close_s.isna().sum() > (len(close_s) * 0.2) or len(close_s.dropna()) < min_days:
            return {"Ticker": ticker, "Action": "Insufficient data", "Price": "N/A", "RSI": "N/A", "MA50": "N/A", "Potential Gain %": "N/A", "Link": ""}

        # compute indicators on the 1D series
        rsi_series = RSIIndicator(close_s).rsi()
        ma50_series = SMAIndicator(close_s, window=50).sma_indicator()
        ma200_series = SMAIndicator(close_s, window=200).sma_indicator()

        # latest values (use .iloc[-1] safely)
        rsi = rsi_series.iloc[-1]
        ma50 = ma50_series.iloc[-1] if len(ma50_series.dropna()) > 0 else np.nan
        price = close_s.iloc[-1]

        # fallback in case of NaNs
        if np.isnan(rsi) or np.isnan(price):
            return {"Ticker": ticker, "Action": "Insufficient indicators", "Price": "N/A", "RSI": "N/A", "MA50": "N/A", "Potential Gain %": "N/A", "Link": ""}

        # Simple rules (you can load rules from JSON instead)
        if (rsi < 30) and (not np.isnan(ma50)) and (price > ma50):
            action = "Buy"
        elif (rsi > 70) and (not np.isnan(ma50)) and (price < ma50):
            action = "Sell"
        else:
            action = "Hold"

        # potential gain example: % between current price and 1y high
        try:
            one_year_high = close_s.max()
            potential_gain = round(((one_year_high - price) / price) * 100, 2)
        except Exception:
            potential_gain = "N/A"

        yahoo_link = f"https://finance.yahoo.com/quote/{ticker}"

        return {
            "Ticker": ticker,
            "Action": action,
            "Price": round(price, 2),
            "RSI": round(rsi, 2),
            "MA50": round(ma50, 2) if not np.isnan(ma50) else "N/A",
            "Potential Gain %": potential_gain,
            "Link": yahoo_link
        }
        #"Link": f'<a href="{yahoo_link}" target="_blank">Yahoo</a>'
    except Exception as e:
        # Return an error row but keep the app running
        return {"Ticker": ticker, "Action": f"Error: {e}", "Price": "N/A", "RSI": "N/A", "MA50": "N/A", "Potential Gain %": "N/A", "Link": ""}

# ---- UI ----
# load tickers
try:
    with open("stocks.txt", "r") as f:
        all_tickers = [line.strip().upper() for line in f if line.strip()]
except FileNotFoundError:
    all_tickers = []

if not all_tickers:
    st.warning("No tickers found in stocks.txt. Add symbols (one per line) to run analysis.")
    st.stop()

st.sidebar.header("Tickers")
selected = st.sidebar.multiselect("Select tickers to analyze", options=all_tickers, default=all_tickers)

st.sidebar.header("Options")
min_days = st.sidebar.slider("Minimum historical days required", min_value=30, max_value=250, value=50, step=10)

if not selected:
    st.info("Select at least one ticker from the sidebar.")
    st.stop()

st.info("Running analysis — this may take a few seconds per ticker...")

rows = []
for t in selected:
    row = analyze_ticker(t, min_days=min_days)
    rows.append(row)

df = pd.DataFrame(rows)

# style action column
def color_action(action):
    if action == "Buy":
        return "background-color: #b6f2b6; font-weight: bold;"
    if action == "Sell":
        return "background-color: #f5b7b1; font-weight: bold;"
    if action == "Hold":
        return "background-color: #e0e0e0;"
    return ""

styled = df.style.format(escape="html").applymap(lambda v: color_action(v) if v in ["Buy", "Sell", "Hold"] else "", subset=["Action"])

st.markdown("### Results")
st.markdown(styled.to_html(escape=False), unsafe_allow_html=True)

st.caption("AlphaLayer — PoC. Not financial advice.")

