import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import os
from ta.momentum import RSIIndicator

# -------------------------------
# CONFIGURATION
# -------------------------------
st.set_page_config(page_title="AlphaLayer - Smart Watchlists", page_icon="📈", layout="wide")

WATCHLIST_DIR = "watchlists"  # folder with your .txt files
USE_GOOGLE_SHEET = False      # set to True if you want persistent watchlists via Google Sheets

# -------------------------------
# FUNCTIONS
# -------------------------------

def get_moving_average(series, window):
    return series.rolling(window=window).mean()

def analyze_stock(ticker):
    """Analyze a single stock and return a dictionary of indicators + action."""
    try:
        df = yf.download(ticker, period="6mo", progress=False)
        if df.empty:
            return {"Ticker": ticker, "Error": "No data"}

        df["RSI"] = RSIIndicator(df["Close"]).rsi().squeeze()
        df["MA50"] = get_moving_average(df["Close"], 50)
        df["MA200"] = get_moving_average(df["Close"], 200)

        rsi = df["RSI"].iloc[-1]
        ma50 = df["MA50"].iloc[-1]
        ma200 = df["MA200"].iloc[-1]
        price = df["Close"].iloc[-1]

        # Buy/sell rules
        if rsi < 30 and price > ma50:
            action = "BUY"
        elif rsi > 70 and price < ma50:
            action = "SELL"
        else:
            action = "HOLD"

        return {
            "Ticker": ticker,
            "Price": round(price, 2),
            "RSI": round(rsi, 2),
            "MA50": round(ma50, 2),
            "MA200": round(ma200, 2),
            "Action": action,
            "Link": f"https://finance.yahoo.com/quote/{ticker}",
        }

    except Exception as e:
        return {"Ticker": ticker, "Error": str(e)}

def load_watchlist_from_file(filename):
    with open(os.path.join(WATCHLIST_DIR, filename)) as f:
        return [line.strip().upper() for line in f if line.strip()]

# -------------------------------
# SIDEBAR: WATCHLISTS
# -------------------------------
st.sidebar.title("📋 Watchlists")

if not os.path.exists(WATCHLIST_DIR):
    os.makedirs(WATCHLIST_DIR)
    with open(os.path.join(WATCHLIST_DIR, "alphalayermaster.txt"), "w") as f:
        f.write("AAPL\nMSFT\nGOOGL\nNVDA\nTSLA\n")

# Load available lists
available_lists = [f for f in os.listdir(WATCHLIST_DIR) if f.endswith(".txt")]
selected_list = st.sidebar.selectbox("Choose a shared watchlist", available_lists)

tickers = load_watchlist_from_file(selected_list)

# Allow custom list
st.sidebar.markdown("---")
st.sidebar.subheader("🧠 Create Your Own Watchlist")
user_tickers = st.sidebar.text_area("Enter tickers (comma-separated)", "AAPL, MSFT, TSLA")
custom_watchlist = [t.strip().upper() for t in user_tickers.split(",") if t.strip()]

if st.sidebar.button("Use My Watchlist"):
    tickers = custom_watchlist
    st.sidebar.success("✅ Using your custom watchlist.")

# -------------------------------
# MAIN DASHBOARD
# -------------------------------
st.title("💹 AlphaLayer — Smarter Stock Insights")
st.caption("An augmented knowledge layer for data-driven investors.")

st.markdown("### 📘 Indicator Descriptions")
st.markdown("""
- **RSI (Relative Strength Index):** Measures momentum — below 30 may signal oversold (buy), above 70 overbought (sell).  
- **MA50 / MA200:** Moving averages — help identify short-term and long-term trends.  
- **Signals:**  
    🟢 **BUY** = RSI < 30 & Price > MA50  
    🔴 **SELL** = RSI > 70 & Price < MA50  
    ⚪ **HOLD** = Otherwise  
""")

st.markdown("---")
st.subheader(f"📊 Analyzing Watchlist: `{selected_list.replace('.txt', '')}`")

results = []
for ticker in tickers:
    result = analyze_stock(ticker)
    results.append(result)

df = pd.DataFrame(results)

if "Error" in df.columns:
    df = df.dropna(subset=["Error"])

if not df.empty:
    # Add colors and clickable links
    def style_row(row):
        color = "green" if row["Action"] == "BUY" else "red" if row["Action"] == "SELL" else "gray"
        return [f"color: {color}"] * len(row)

    df["Ticker"] = df.apply(lambda x: f"[{x['Ticker']}]({x['Link']})", axis=1)

    st.dataframe(
        df[["Ticker", "Price", "RSI", "MA50", "MA200", "Action"]],
        use_container_width=True,
    )
else:
    st.warning("No valid stock data found.")

st.markdown("---")
st.caption("💡 *AlphaLayer — Turning signals into insight.*")
