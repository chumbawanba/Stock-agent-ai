import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands

# ---------------- CONFIG ---------------- #
WATCHLIST_DIR = "watchlists"
if not os.path.exists(WATCHLIST_DIR):
    os.makedirs(WATCHLIST_DIR)

DEFAULT_LISTS = ["Watch_list", "wl_edgar", "wl_tiago"]

# Ensure the three lists exist
for filename in DEFAULT_LISTS:
    path = os.path.join(WATCHLIST_DIR, filename)
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("AAPL\nMSFT\nGOOGL\n")
    
RULES_FILE = "rules.json"

# ---------------- INDICATORS ---------------- #
def compute_indicators(df):
    """Compute technical indicators for a given dataframe."""
    df["RSI"] = RSIIndicator(df["Close"].squeeze()).rsi()
    df["MA50"] = df["Close"].rolling(window=50).mean()
    df["MA200"] = df["Close"].rolling(window=200).mean()
    df["EMA20"] = EMAIndicator(df["Close"], window=20).ema_indicator()

    macd = MACD(df["Close"])
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()

    boll = BollingerBands(df["Close"])
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
    try:
        df = yf.download(ticker, period="6mo", progress=False)
        if df.empty:
            return None

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
            "MACD": round(MACD, 2),
            "MACD_Signal": round(MACD_Signal, 2),
            "Signal": signal,
            "Link": f"https://finance.yahoo.com/quote/{ticker}"
        }

    except Exception:
        return None


# ---------------- STREAMLIT UI ---------------- #
st.set_page_config(page_title="AlphaLayer", page_icon="💹", layout="wide")

st.title("💹 AlphaLayer — Smarter Stock Insights")
st.markdown("### An augmented knowledge layer for data-driven investors.")

with st.expander("📘 Indicator Descriptions"):
    st.markdown("""
    **RSI (Relative Strength Index):** Measures momentum — below 30 may signal oversold (buy), above 70 overbought (sell).  
    **MA50 / MA200:** Moving averages — help identify short-term and long-term trends.  
    **EMA20:** Exponential moving average, more sensitive to recent prices.  
    **MACD:** Momentum indicator comparing two EMAs; helps detect trend changes.  
    **Bollinger Bands:** Measure volatility; prices near lower band may be undervalued.
    """)

# ----- Sidebar Controls -----
st.sidebar.header("⚙️ Customize Settings")

# Select watchlist
selected_watchlist = st.sidebar.selectbox("Choose a watchlist", DEFAULT_LISTS)

# Manage symbols
symbols = load_watchlist(selected_watchlist)
new_symbol = st.sidebar.text_input("➕ Add Symbol (e.g., AAPL)")

if st.sidebar.button("Add Symbol"):
    if new_symbol and new_symbol not in symbols:
        symbols.append(new_symbol.upper())
        save_watchlist(selected_watchlist, symbols)
        st.sidebar.success(f"Added {new_symbol.upper()} to {selected_watchlist}")

remove_symbol = st.sidebar.selectbox("🗑️ Remove Symbol", [""] + symbols)
if st.sidebar.button("Remove Symbol") and remove_symbol:
    symbols.remove(remove_symbol)
    save_watchlist(selected_watchlist, symbols)
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

# ----- Analyze stocks -----
if st.button("🔍 Analyze Watchlist"):
    st.subheader(f"📊 Analyzing Watchlist: {selected_watchlist}")
    results = []
    for ticker in symbols:
        res = analyze_stock(ticker, rules)
        if res:
            results.append(res)

    if results:
        df = pd.DataFrame(results)
        df["Ticker"] = df.apply(lambda x: f"[{x['Ticker']}]({x['Link']})", axis=1)
        df = df.drop(columns=["Link"])

        # Apply colors
        def color_signal(val):
            if "BUY" in val:
                return "background-color: #d4edda; color: green"
            elif "SELL" in val:
                return "background-color: #f8d7da; color: red"
            else:
                return ""

        styled = df.style.applymap(color_signal, subset=["Signal"])
        st.dataframe(df[["Ticker", "Price", "RSI", "MA50", "Signal"]], use_container_width=True)
    else:
        st.warning("⚠️ No valid stock data found. Check tickers or rules.")
else:
    st.info("Select a watchlist and click 'Analyze Watchlist' to begin.")


