import streamlit as st
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
import datetime

# --- Page config ---
st.set_page_config(page_title="AlphaLayer - Stock Signals", layout="wide")

# --- Load ticker list ---
TICKER_FILE = "stocks.txt"

def load_tickers():
    try:
        with open(TICKER_FILE, "r") as f:
            tickers = [line.strip().upper() for line in f if line.strip()]
        return tickers
    except FileNotFoundError:
        return []

# --- Analyze Stock ---
def check_stock(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d")

        # ✅ Flatten 2D arrays (fix for tickers like BRK-B, BF-B)
        df["Close"] = df["Close"].squeeze()

        # Compute indicators
        df["rsi"] = RSIIndicator(df["Close"]).rsi()
        df["ma50"] = df["Close"].rolling(window=50).mean()
        df["ma200"] = df["Close"].rolling(window=200).mean()

        latest = df.iloc[-1]

        action = "Hold"
        reason = "No clear signal."
        potential_return = 0

        if latest["rsi"] < 30 and latest["Close"] > latest["ma50"]:
            action = "Buy"
            reason = "RSI is low and price is above MA50 — potential uptrend."
            potential_return = ((latest["ma200"] - latest["Close"]) / latest["Close"]) * 100
        elif latest["rsi"] > 70 and latest["Close"] < latest["ma50"]:
            action = "Sell"
            reason = "RSI is high and price fell below MA50 — potential downtrend."
            potential_return = ((latest["Close"] - latest["ma200"]) / latest["Close"]) * 100

        return {
            "Symbol": ticker,
            "Action": action,
            "Reason": reason,
            "Potential Return (%)": round(potential_return, 2)
        }

    except Exception as e:
        return {
            "Symbol": ticker,
            "Action": "Error",
            "Reason": f"Error analyzing {ticker}: {str(e)}",
            "Potential Return (%)": 0
        }

# --- UI ---
st.title("📈 AlphaLayer")
st.subheader("Augmented Intelligence for Smarter Stock Signals")

st.markdown("---")

tickers = load_tickers()
if not tickers:
    st.warning("No tickers found. Please add tickers to `stocks.txt`.")
    st.stop()

data_rows = []
for ticker in tickers:
    result, _ = analyze_stock(ticker)
    if result:
        data_rows.append(result)

if not data_rows:
    st.error("No data available to display.")
    st.stop()

df_display = pd.DataFrame(data_rows)

# Apply color formatting
def highlight_signal(val, color):
    return f"color: white; background-color: {color}; font-weight: bold"

colors = df_display["Color"]
df_display_styled = df_display.drop(columns=["Color"]).style.apply(
    lambda _: [highlight_signal(sig, col) for sig, col in zip(df_display["Signal"], colors)],
    axis=1
)

st.dataframe(df_display_styled, use_container_width=True)

# Footer
st.markdown("---")
st.caption("💡 This is a Proof-of-Concept (PoC) powered by Streamlit & yFinance — not financial advice.")

