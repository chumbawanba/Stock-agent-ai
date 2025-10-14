import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
import io
import base64
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
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    if "Close" not in df.columns:
        raise ValueError("Missing 'Close' column in DataFrame")

    close = df["Close"]
    if hasattr(close.values[0], "__len__") and not isinstance(close.values[0], (float, int)):
        close = pd.Series(close.squeeze(), index=df.index)

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


# ---------------- MINI CHART (SPARKLINE) ---------------- #
def make_sparkline(ticker):
    """Create a small price trend plot as base64 image for embedding in table."""
    try:
        data = yf.download(ticker, period="3mo", progress=False)
        if data.empty:
            return ""
        fig, ax = plt.subplots(figsize=(2.5, 0.6))
        ax.plot(data.index, data["Close"], linewidth=1.2, color="steelblue")
        ax.axis("off")

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)
        plt.close(fig)
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode()
        return f'<img src="data:image/png;base64,{img_b64}" width="100"/>'
    except Exception:
        return ""


# ---------------- STOCK ANALYSIS ---------------- #
def analyze_stock(ticker, rules):
    ticker_fixed = ticker.replace("-", ".").strip().upper()
    try:
        df = yf.download(ticker_fixed, period="6mo", progress=False)
        if df.empty:
            st.warning(f"⚠️ No data returned for {ticker_fixed}")
            return None

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
            "Ticker": ticker_fixed,
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

# ----- Sidebar Controls ----- #
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

# ----- Analyze Stocks ----- #
if st.button("🔍 Analyze Watchlist"):
    st.subheader(f"📊 Analyzing Watchlist: {selected_watchlist}")
    results = []
    for ticker in symbols:
        res = analyze_stock(ticker, rules)
        if res:
            results.append(res)
        else:
            st.warning(f"⚠️ Could not analyze {ticker}")

    if results:
        df = pd.DataFrame(results)

        # Add sparklines
        st.text("Generating trend previews...")
        df["Trend"] = df["Ticker"].apply(lambda t: make_sparkline(t))

        # Format numeric values
        df["Price"] = df["Price"].apply(lambda x: f"${x:,.2f}")
        for col in ["RSI", "MA50", "MA200", "MACD", "MACD_Signal"]:
            df[col] = df[col].apply(lambda x: f"{x:.2f}")

        # Add Yahoo links
        df["Yahoo Link"] = df["Link"].apply(lambda l: f'<a href="{l}" target="_blank">🔗 Open</a>')
        df = df.drop(columns=["Link"])

        # Reorder columns
        df = df[["Ticker", "Trend", "Price", "RSI", "MA50", "MA200", "MACD", "MACD_Signal", "Signal", "Yahoo Link"]]

        # Color-coded signals
        def color_signal(val):
            if "BUY" in val:
                return "background-color: #d4edda; color: green; font-weight: bold"
            elif "SELL" in val:
                return "background-color: #f8d7da; color: red; font-weight: bold"
            else:
                return "background-color: #f0f0f0; color: gray"

        styled_html = df.to_html(escape=False, index=False)
        styled_html = styled_html.replace("<td>🟢 BUY</td>", '<td style="background:#d4edda; color:green; font-weight:bold;">🟢 BUY</td>')
        styled_html = styled_html.replace("<td>🔴 SELL</td>", '<td style="background:#f8d7da; color:red; font-weight:bold;">🔴 SELL</td>')
        styled_html = styled_html.replace("<td>⚪ HOLD</td>", '<td style="background:#f0f0f0; color:gray; font-weight:bold;">⚪ HOLD</td>')

        st.markdown("### 📋 Analysis Results")
        st.markdown("<style>table {width:100%; border-collapse:collapse;} th, td {padding:8px; text-align:center;} tr:nth-child(even){background:#f9f9f9;}</style>", unsafe_allow_html=True)
        st.markdown(styled_html, unsafe_allow_html=True)
    else:
        st.info("No valid data to display.")
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

