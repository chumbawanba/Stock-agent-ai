import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from datetime import datetime

def check_stock(ticker: str) -> str:
    # Download last 6 months of daily data
    df = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True)
    if df.empty:
        return f"{ticker}: No data found."
    
    # Calculate indicators
    df["rsi"] = RSIIndicator(df["Close"]).rsi()
    df["ma50"] = df["Close"].rolling(window=50).mean()
    df["ma200"] = df["Close"].rolling(window=200).mean()
    
    # Get latest values
    latest = df.iloc[-1]
    rsi = latest["rsi"]
    close = latest["Close"]
    ma50 = latest["ma50"]
    ma200 = latest["ma200"]
    
    # Apply rules
    if rsi < 30 and close > ma50:
        decision = "BUY"
    elif rsi > 70 or close < ma200:
        decision = "SELL"
    else:
        decision = "HOLD"
    
    return f"{ticker}: {decision} (RSI={rsi:.2f}, Price={close:.2f})", {
        "Ticker": ticker,
        "Decision": decision,
        "RSI": round(rsi, 2),
        "Price": round(close, 2),
        "MA50": round(ma50, 2),
        "MA200": round(ma200, 2),
        "Date": datetime.today().strftime("%Y-%m-%d")
    }

# List of tickers to check
tickers = ["AAPL", "TSLA", "NVDA", "GOOGL", "MSFT"]

# Store results for CSV
results = []

# Check each stock
for ticker in tickers:
    text, data = check_stock(ticker)
    print(text)
    results.append(data)

# Save to CSV
df_results = pd.DataFrame(results)
df_results.to_csv("stock_report.csv", index=False)




