import streamlit as st
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

st.set_page_config(page_title="AlphaLayer", page_icon="📊", layout="wide")

st.title("💹 AlphaLayer — Augmented Market Insights")

st.markdown(
    """
    Welcome to **AlphaLayer** — your intelligent investment assistant.  
    This Proof of Concept analyzes stocks using basic RSI & SMA indicators,  
    and highlights *Buy / Sell / Hold* opportunities.
    """
)

# --- Load ticker list from GitHub file ---
try:
    with open("stocks.txt") as f:
        tickers = [line.strip().upper() for line in f if line.strip()]
except FileNotFoundError:
    tickers = ["AAPL", "MSFT", "TSLA", "NVDA", "AMZN"]

st.sidebar.header("📋 Settings")
selected_tickers = st.sidebar.multiselect("Select stocks to analyze", tickers, default=tickers)

# --- Function to analyze one stock ---
def analyze_stock(ticker):
    try:
        df = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if df.empty:
            return f"No data for {ticker}", None

        # Ensure columns are 1D
        for col in ["Close"]:
            df[col] = df[col].squeeze()

        # Calculate indicators
        df["rsi"] = RSIIndicator(df["Close"].astype(float)).rsi()
        df["ma50"] = SMAIndicator(df["Close"].astype(float), window=50).sma_indicator()

        latest = df.iloc[-1]

        # Rules for Buy/Sell/Hold
        if latest["rsi"] < 30 and latest["Close"] > latest["ma50"]:
            action = "Buy"
        elif latest["rsi"] > 70 and latest["Close"] < latest["ma50"]:
            action = "Sell"
        else:
            action = "Hold"

        # Potential gain (simple last-year gain)
        past_year = yf.download(ticker, period="1y", interval="1d", progress=False)
        potential_gain = (
            (latest["Close"] / past_year["Close"].iloc[0] - 1) * 100 if not past_year.empty else 0
        )

        return {
            "Ticker": ticker,
            "Price": round(latest["Close"], 2),
            "RSI": round(latest["rsi"], 2),
            "MA50": round(latest["ma50"], 2),
            "Action": action,
            "Potential Gain %": round(potential_gain, 2),
            "Yahoo Finance": f'<a href="https://finance.yahoo.com/quote/{ticker}" target="_blank">🔗 Link</a>'
        }

    except Exception as e:
        return {"Ticker": ticker, "Action": f"Error: {str(e)}"}

# --- Run analysis ---
results = [analyze_stock(t) for t in selected_tickers if t]

# --- Filter out None results ---
data = [r for r in results if isinstance(r, dict)]
if not data:
    st.warning("No valid stock data found.")
else:
    df = pd.DataFrame(data)

    # --- Styling ---
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
    st.markdown(styled_df.to_html(escape=False), unsafe_allow_html=True)
    st.caption("💡 *AlphaLayer helps you make sense of the markets with data-driven clarity.*")

