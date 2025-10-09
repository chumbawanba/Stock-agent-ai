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
def analyze_stock(ticker):
    try:
        end = datetime.date.today()
        start = end - datetime.timedelta(days=365 * 2)  # 2 years of data
        df = yf.download(ticker, start=start, end=end)

        if df.empty:
            return None, None

        df["rsi"] = RSIIndicator(close=df["Close"]).rsi()
        df["ma50"] = SMAIndicator(close=df["Close"], window=50).sma_indicator()

        latest = df.iloc[-1]
        action = "HOLD"
        color = "gray"

        if latest["rsi"] < 30 and latest["Close"] > latest["ma50"]:
            action = "BUY"
            color = "green"
        elif latest["rsi"] > 70 and latest["Close"] < latest["ma50"]:
            action = "SELL"
            color = "red"

        yahoo_link = f"https://finance.yahoo.com/quote/{ticker}"
        return {
            "Ticker": f"[{ticker}]({yahoo_link})",
            "Price": f"${latest['Close']:.2f}",
            "RSI": f"{latest['rsi']:.2f}",
            "MA50": f"${latest['ma50']:.2f}",
            "Signal": action,
            "Color": color
        }, df

    except Exception as e:
        st.error(f"Error analyzing {ticker}: {e}")
        return None, None

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

