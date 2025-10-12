import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import os
from ta.momentum import RSIIndicator

# -------------------------------
# CONFIGURATION
# -------------------------------
st.set_page_config(page_title="AlphaLayer Watchlists", page_icon="📈", layout="wide")

WATCHLIST_DIR = "watchlists"
if not os.path.exists(WATCHLIST_DIR):
    os.makedirs(WATCHLIST_DIR)

DEFAULT_LISTS = ["tech.txt", "growth.txt", "dividend.txt"]

# Ensure the three lists exist
for filename in DEFAULT_LISTS:
    path = os.path.join(WATCHLIST_DIR, filename)
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("AAPL\nMSFT\nGOOGL\n")

# -------------------------------
# FUNCTIONS
# -------------------------------

def get_moving_average(series, window):
    return series.rolling(window=window).mean()

def analyze_stock(ticker):
    """Analyze one stock and return basic buy/sell/hold signals."""
    try:
        df = yf.download(ticker, period="6mo", progress=False)
        if df.empty:
            return {"Ticker": ticker, "Error": "No data", "Link": f"https://finance.yahoo.com/quote/{ticker}"}

        df["RSI"] = RSIIndicator(df["Close"].squeeze()).rsi()
        df["MA50"] = get_moving_average(df["Close"], 50)
        df["MA200"] = get_moving_average(df["Close"], 200)

        rsi = float(df["RSI"].iloc[-1])
        ma50 = float(df["MA50"].iloc[-1])
        price = float(df["Close"].iloc[-1])

        if rsi < 30 and price > ma50:
            action = "🟢 BUY"
        elif rsi > 70 and price < ma50:
            action = "🔴 SELL"
        else:
            action = "⚪ HOLD"

        return {
            "Ticker": ticker,
            "Price": round(price, 2),
            "RSI": round(rsi, 2),
            "MA50": round(ma50, 2),
            "Action": action,
            "Link": f"https://finance.yahoo.com/quote/{ticker}",
        }

    except Exception as e:
        return {"Ticker": ticker, "Error": str(e), "Link": f"https://finance.yahoo.com/quote/{ticker}"}

def load_watchlist(filename):
    path = os.path.join(WATCHLIST_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [line.strip().upper() for line in f if line.strip()]

def save_watchlist(filename, tickers):
    path = os.path.join(WATCHLIST_DIR, filename)
    with open(path, "w") as f:
        f.write("\n".join(sorted(set(tickers))))

# -------------------------------
# SIDEBAR
# -------------------------------
st.sidebar.title("📋 Manage Watchlists")

selected_file = st.sidebar.selectbox("Choose a watchlist", DEFAULT_LISTS)

tickers = load_watchlist(selected_file)

# Add ticker
new_ticker = st.sidebar.text_input("Add new ticker (e.g. NVDA)")
if st.sidebar.button("➕ Add Ticker"):
    if new_ticker.strip():
        tickers.append(new_ticker.strip().upper())
        save_watchlist(selected_file, tickers)
        st.sidebar.success(f"Added {new_ticker.upper()} to {selected_file}")

# Remove ticker
if tickers:
    remove_ticker = st.sidebar.selectbox("Remove a ticker", [""] + tickers)
    if st.sidebar.button("🗑️ Remove Selected"):
        if remove_ticker:
            tickers = [t for t in tickers if t != remove_ticker]
            save_watchlist(selected_file, tickers)
            st.sidebar.warning(f"Removed {remove_ticker} from {selected_file}")

# -------------------------------
# MAIN DASHBOARD
# -------------------------------
st.title("💹 AlphaLayer — Simple Watchlists")
st.caption("Smarter insights, simplified.")

st.markdown("""
### 📘 Indicator Descriptions
- **RSI (Relative Strength Index):** Measures momentum — below 30 = oversold, above 70 = overbought.  
- **MA50:** 50-day moving average — short-term trend.  
- **Signals:**  
    🟢 **BUY** = RSI < 30 & Price > MA50  
    🔴 **SELL** = RSI > 70 & Price < MA50  
    ⚪ **HOLD** = Otherwise  
""")

st.markdown("---")
st.subheader(f"📊 Watchlist: `{selected_file.replace('.txt', '').capitalize()}`")

results = [analyze_stock(t) for t in tickers]
df = pd.DataFrame(results)

# Handle errors
if "Error" in df.columns and df["Error"].notna().any():
    with st.expander("⚠️ Some tickers had issues"):
        st.write(df[df["Error"].notna()][["Ticker", "Error"]])

# Show valid data only
df = df[df["Error"].isna()] if "Error" in df.columns else df

if not df.empty:
    df["Ticker"] = df.apply(
        lambda x: f"[{x['Ticker']}]({x['Link']})", axis=1
    )
    st.dataframe(df[["Ticker", "Price", "RSI", "MA50", "Action"]], use_container_width=True)
else:
    st.info("No valid data to display.")

st.markdown("---")
st.caption("💡 *AlphaLayer — Clear signals, smarter investing.*")


