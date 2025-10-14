import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import matplotlib.pyplot as plt
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands

# ---------------- CONFIG ---------------- #
WATCHLIST_DIR = "watchlists"
if not os.path.exists(WATCHLIST_DIR):
    os.makedirs(WATCHLIST_DIR)

DEFAULT_LISTS = ["wl_default.txt", "wl_edgar.txt", "wl_tiago.txt"]

# Ensure the three lists exist
for filename in DEFAULT_LISTS:
    path = os.path.join(WATCHLIST_DIR, filename)
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("AAPL\nMSFT\nGOOGL\n")

WATCHLIST_CHOICES = [name.replace(".txt", "") for name in DEFAULT_LISTS]
RULES_FILE = "rules.json"

# ---------------- INDICATORS ---------------- #
def compute_indicators(df):
    """Compute technical indicators for a given dataframe safely."""
    # Ensure Close column is a clean 1D Series
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]  # flatten MultiIndex

    if "Close" not in df.columns:
        raise ValueError("Missing 'Close' column in DataFrame")

    close = df["Close"]

    # If Close is 2D (e.g., [[100],[101],...]) => flatten to 1D
    if hasattr(close.values[0], "__len__") and not isinstance(close.values[0], (float, int)):
        close = pd.Series(close.squeeze(), index=df.index)

    # Compute indicators
    df["RSI"] = RSIIndicator(close).rsi()
    df["MA50"] = close.rolling(window=50).mean()
    df["MA200"] = close.rolling(window=200).mean()
    df["EMA20"] = EMAIndicator(close, window=20).ema_indicator()

    macd = MACD(close)
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()

    boll = BollingerBands(close)
    df["Boll_Upper"] = boll.bollinger_hband()
    df["Boll_Lower"] = boll.bollinger_lband()

    return df


# ---------------- RULES ---------------- #
def load_rules():
    try:
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        default_rules = {
            "BUY": "RSI < 30 and Price > MA50 and MACD > MACD_Signal",
            "SELL": "RSI > 70 and Price < MA50 and MACD < MACD_Signal"
        }
        save_rules(default_rules)
        return default_rules

def save_rules(rules):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=2)


# ---------------- WATCHLISTS ---------------- #
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


# ---------------- STOCK ANALYSIS ---------------- #

def analyze_stock(ticker, rules):
    ticker_fixed = ticker.replace("-", ".").strip().upper()
    try:
        df = yf.download(ticker_fixed, period="6mo", progress=False)
        if df.empty:
            st.warning(f"⚠️ No data returned for {ticker_fixed}")
            return None


        # Ensure 1D arrays
        if isinstance(df["Close"].values[0], (list, tuple)) or hasattr(df["Close"].values[0], "__len__"):
            df["Close"] = df["Close"].squeeze()

        df = compute_indicators(df)
        latest = df.iloc[-1]

        Price = latest["Close"]
        RSI = latest["RSI"]
        MA50 = latest["MA50"]
        MA200 = latest["MA200"]
        EMA20 = latest["EMA20"]
        MACD = latest["MACD"]
        MACD_Signal = latest["MACD_Signal"]

        # Evaluate user rules
        try:
            if eval(rules["BUY"]):
                signal = "🟢 BUY"
            elif eval(rules["SELL"]):
                signal = "🔴 SELL"
            else:
                signal = "⚪ HOLD"
        except Exception as e:
            signal = f"⚠️ Rule Error: {e}"

        return {
            "Ticker": ticker,
            "Price": round(Price, 2),
            "RSI": round(RSI, 2),
            "MA50": round(MA50, 2),
            "MA200": round(MA200, 2),
            "EMA20": round(EMA20, 2),
            "MACD": round(MACD, 2),
            "MACD_Signal": round(MACD_Signal, 2),
            "Signal": signal,
            "Link": f"https://finance.yahoo.com/quote/{ticker_fixed}"
        }

    except Exception as e:
        st.error(f"❌ Error analyzing {ticker_fixed}: {e}")
        return None


# ---------------- STREAMLIT UI ---------------- #
st.set_page_config(page_title="AlphaLayer", page_icon="💹", layout="wide")

st.title("💹 AlphaLayer — Smarter Stock Insights")
st.markdown("### An augmented knowledge layer for data-driven investors.")



# ----- Sidebar Controls -----
st.sidebar.header("⚙️ Customize Settings")

# Select watchlist
selected_watchlist = st.sidebar.selectbox("Choose a watchlist", WATCHLIST_CHOICES)
symbols = load_watchlist(f"{selected_watchlist}.txt")

# Manage symbols
new_symbol = st.sidebar.text_input("➕ Add Symbol (e.g., AAPL)")

if st.sidebar.button("Add Symbol"):
    if new_symbol and new_symbol.upper() not in symbols:
        symbols.append(new_symbol.upper())
        save_watchlist(f"{selected_watchlist}.txt", symbols)
        st.sidebar.success(f"Added {new_symbol.upper()} to {selected_watchlist}")

remove_symbol = st.sidebar.selectbox("🗑️ Remove Symbol", [""] + symbols)
if st.sidebar.button("Remove Symbol") and remove_symbol:
    symbols.remove(remove_symbol)
    save_watchlist(f"{selected_watchlist}.txt", symbols)
    st.sidebar.success(f"Removed {remove_symbol}")

# Rules editor
rules = load_rules()
st.sidebar.subheader("🧠 Trading Rules")
buy_rule = st.sidebar.text_area("BUY Rule", value=rules["BUY"], height=80)
sell_rule = st.sidebar.text_area("SELL Rule", value=rules["SELL"], height=80)

if st.sidebar.button("💾 Save Rules"):
    rules["BUY"] = buy_rule
    rules["SELL"] = sell_rule
    save_rules(rules)
    st.sidebar.success("Rules saved successfully!")


import time

FAILED_LOG = "failed_tickers.txt"

# ----- Analyze stocks -----
if st.button("🔍 Analyze Watchlist"):
    st.session_state["analyzed_data"] = []  # Reset stored results
    st.session_state["selected_watchlist"] = selected_watchlist

    st.subheader(f"📊 Analyzing Watchlist: {selected_watchlist}")
    results = []
    for ticker in load_watchlist(selected_watchlist):
        res = analyze_stock(ticker, load_rules())
        if res:
            results.append(res)
        else:
            st.warning(f"⚠️ Could not analyze {ticker}")

    if results:
        st.session_state["analyzed_data"] = pd.DataFrame(results)

# --- Display cached results ---
if "analyzed_data" in st.session_state and not st.session_state["analyzed_data"].empty:
    df = st.session_state["analyzed_data"].copy()

    # Format columns
    df["Price"] = df["Price"].apply(lambda x: f"${x:,.2f}")
    for col in ["RSI", "MA50", "MA200", "MACD", "MACD_Signal"]:
        df[col] = df[col].apply(lambda x: f"{x:.2f}")
    df["Yahoo Link"] = df["Link"].apply(lambda l: f"[Open]({l})")
    df = df.drop(columns=["Link"])

    df = df[
        ["Ticker", "Price", "RSI", "MA50", "MA200", "MACD", "MACD_Signal", "Signal", "Yahoo Link"]
    ]

    # Color signals
    def color_signal(val):
        if "BUY" in val:
            return "background-color: #d4edda; color: green; font-weight: bold"
        elif "SELL" in val:
            return "background-color: #f8d7da; color: red; font-weight: bold"
        else:
            return "background-color: #f0f0f0; color: gray"

    styled = (
        df.style
        .applymap(color_signal, subset=["Signal"])
        .set_properties(**{"text-align": "center", "border": "1px solid #ddd", "padding": "6px"})
    )

    st.markdown("### 📋 Analysis Results")
    st.dataframe(df, use_container_width=True)

    # --- Chart section ---
    st.markdown("---")
    st.subheader("📈 View Stock Chart")

    selected_ticker = st.selectbox("Choose a stock to view chart:", df["Ticker"].tolist(), key="chart_select")

    if selected_ticker:
        import matplotlib.pyplot as plt

        data = yf.download(selected_ticker, period="1y", progress=False)
        if not data.empty:
            data["MA50"] = data["Close"].rolling(window=50).mean()
            data["MA200"] = data["Close"].rolling(window=200).mean()

            st.markdown(f"### {selected_ticker} — Price with MA50 / MA200")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(data.index, data["Close"], label="Close", linewidth=1.8)
            ax.plot(data.index, data["MA50"], label="MA50", linestyle="--")
            ax.plot(data.index, data["MA200"], label="MA200", linestyle=":")
            ax.set_title(f"{selected_ticker} Price Trend")
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)

            st.markdown(f"[🔗 View on Yahoo Finance](https://finance.yahoo.com/quote/{selected_ticker})")
else:
    st.info("Select a watchlist and click 'Analyze Watchlist' to begin.")
    
with st.expander("📘 Indicator Descriptions"):
    st.markdown("""
    **RSI (Relative Strength Index):** Measures momentum — below 30 may signal oversold (buy), above 70 overbought (sell).  
    **MA50 / MA200:** Moving averages — help identify short-term and long-term trends.  
    **EMA20:** Exponential moving average, more sensitive to recent prices.  
    **MACD:** Momentum indicator comparing two EMAs; helps detect trend changes.  
    **Bollinger Bands:** Measure volatility; prices near lower band may be undervalued.
    """)
