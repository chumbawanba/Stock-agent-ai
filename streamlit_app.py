import streamlit as st
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

# -------------------------------
# Core Stock Analysis Logic
# -------------------------------
def check_stock(ticker):
    try:
        df = yf.download(ticker, period="1y", progress=False)
        if df.empty:
            return {"Symbol": ticker, "Action": "No Data", "Potential Gain (%)": "N/A", "Yahoo Link": ""}

        df["Close"] = df["Close"].astype(float)
        df["rsi"] = RSIIndicator(df["Close"]).rsi()
        df["ma50"] = SMAIndicator(df["Close"], window=50).sma_indicator()
        df["ma200"] = SMAIndicator(df["Close"], window=200).sma_indicator()

        latest = df.iloc[-1]
        close = latest["Close"]
        rsi = latest["rsi"]
        ma50 = latest["ma50"]
        ma200 = latest["ma200"]

        # Generate simple buy/sell rules
        if rsi < 30 and close > ma50:
            action = "Buy"
        elif rsi > 70 and close < ma50:
            action = "Sell"
        else:
            action = "Hold"

        # Estimate potential gain based on 1y high vs current
        year_high = df["Close"].max()
        potential_gain = round(((year_high - close) / close) * 100, 2)

        yahoo_link = f"https://finance.yahoo.com/quote/{ticker}"
        return {
            "Symbol": ticker,
            "Actions": action,
            "Potential Gain (%)": potential_gain,
            "Yahoo Link": yahoo_link
        }
    except Exception as e:
        return {"Symbol": ticker, "Action": f"Error: {str(e)}", "Potential Gain (%)": "N/A", "Yahoo Link": ""}

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="AlphaLayer — Smart Stock Insights", page_icon="📈", layout="wide")

st.title("📊 AlphaLayer — Augmented Market Intelligence")
st.markdown("### Smarter, faster insights powered by data & logic, not hype.")

# Load tickers from file
try:
    with open("stocks.txt", "r") as f:
        tickers = [line.strip() for line in f.readlines() if line.strip()]
except FileNotFoundError:
    st.error("⚠️ 'stocks.txt' file not found. Please create one with ticker symbols (one per line).")
    st.stop()

#st.sidebar.header("📁 Stock List")
#st.sidebar.write(f"Loaded **{len(tickers)}** tickers from `stocks.txt`")

# Analyze
st.write("Analyzing market signals... please wait ⏳")

results = [check_stock(ticker) for ticker in tickers]
df = pd.DataFrame(results)

# Add clickable links
df["Yahoo Link"] = df["Yahoo Link"].apply(
    lambda x: f"[🔗 Open]({x})" if isinstance(x, str) and x != "" else ""
)

# Highlight actions
def highlight_action(val):
    if val == "Buy":
        return "background-color: #b6f2b6"  # green
    elif val == "Sell":
        return "background-color: #f5b7b1"  # red
    elif val == "Hold":
        return "background-color: #e0e0e0"  # gray
    return ""

styled_df = df.style.applymap(highlight_action, subset=["Action"])

st.markdown("### 📈 Market Overview")

# Render styled DataFrame as HTML (supports colors + links)
st.markdown(styled_df.to_html(escape=False), unsafe_allow_html=True)

st.caption("💡 *AlphaLayer helps you make sense of the markets with data-driven clarity.*")


