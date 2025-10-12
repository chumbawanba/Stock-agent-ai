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

WATCHLIST_DIR = "watchlists"
if not os.path.exists(WATCHLIST_DIR):
    os.makedirs(WATCHLIST_DIR)
    with open(os.path.join(WATCHLIST_DIR, "stocks.txt"), "w") as f:
        f.write("AAPL\nMSFT\nGOOGL\nNVDA\nTSLA\n")

# -------------------------------
# FUNCTIONS
# -------------------------------

def get_moving_average(series, window):
    return series.rolling(window=window).mean()

def analyze_stock(ticker):
    """Analyze one stock and return indicators + suggested action."""
    try:
        df = yf.download(ticker, period="6mo", progress=False)
        if df.empty:
            return {"Ticker": ticker, "Error": "No data", "Link": f"https://finance.yahoo.com/quote/{ticker}"}

        df["RSI"] = RSIIndicator(df["Close"]).rsi().squeeze()
        df["MA50"] = get_moving_average(df["Close"], 50)
        df["MA200"] = get_moving_average(df["Close"], 200)

        rsi = float(df["RSI"].iloc[-1])
        ma50 = float(df["MA50"].iloc[-1])
        ma200 = float(df["MA200"].iloc[-1])
        price = float(df["Close"].iloc[-1])

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
        return {"Ticker": ticker, "Error": str(e), "Link": f"https://finance.yahoo.com/quote/{ticker}"}

def load_watchlist_from_file(filename):
    path = os.path.join(WATCHLIST_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [line.strip().upper() for line in f if line.strip()]

# -------------------------------
# SIDEBAR
# -------------------------------
st.sidebar.title("📋 Watchlists")

available_lists = [f for f in os.listdir(WATCHLIST_DIR) if f.endswith(".txt")]
selected_list = st.sidebar.selectbox("Choose a shared watchlist", available_lists)

tickers = load_watchlist_from_file(selected_list)

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
- **MA50 / MA200:** Moving averages — identify short and long-term trends.  
- **Signals:**  
    🟢 **BUY** = RSI < 30 & Price > MA50  
    🔴 **SELL** = RSI > 70 & Price < MA50  
    ⚪ **HOLD** = Otherwise  
""")

st.markdown("---")
st.subheader(f"📊 Analyzing Watchlist: `{selected_list.replace('.txt', '')}`")

results = [analyze_stock(t) for t in tickers]
df = pd.DataFrame(results)

# Drop rows with missing or invalid tickers
df = df.dropna(subset=["Ticker"])

# If there are errors, show them in a collapsible box
error_rows = df[df["Error"].notna()] if "Error" in df.columns else pd.DataFrame()
if not error_rows.empty:
    with st.expander("⚠️ Errors loading some tickers"):
        st.write(error_rows[["Ticker", "Error"]])

# Only show valid results
df = df[df["Error"].isna()] if "Error" in df.columns else df

if not df.empty:
    # Clickable links
    df["Ticker"] = df.apply(
        lambda x: f"[{x['Ticker']}]({x['Link']})" if "Link" in x else x["Ticker"], axis=1
    )

    # Replace action text with colored emojis
    def color_action(action):
        if action == "BUY":
            return "🟢 BUY"
        elif action == "SELL":
            return "🔴 SELL"
        else:
            return "⚪ HOLD"

    df["Action"] = df["Action"].apply(color_action)

    st.dataframe(
        df[["Ticker", "Price", "RSI", "MA50", "MA200", "Action"]],
        use_container_width=True,
    )
else:
    st.warning("No valid stock data found. Check your watchlist tickers.")

st.markdown("---")
st.caption("💡 *AlphaLayer — Turning signals into insight.*")

