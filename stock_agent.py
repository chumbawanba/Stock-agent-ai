import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# ------------------ Email settings from GitHub Secrets ------------------
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_TO = os.environ.get("EMAIL_TO")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# ------------------ Stock rules function ------------------
def check_stock(ticker: str):
    df = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True)
    if df.empty:
        return f"{ticker}: No data found.", None

    # Flatten Close column in case it's 2D
    close_series = df["Close"]
    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.squeeze()

    df["rsi"] = RSIIndicator(close_series).rsi()
    df["ma50"] = df["Close"].rolling(window=50).mean()
    df["ma200"] = df["Close"].rolling(window=200).mean()

    latest = df.iloc[-1]

    # Convert Series to scalar
    rsi = latest["rsi"].item() if hasattr(latest["rsi"], "item") else latest["rsi"]
    close = latest["Close"].item() if hasattr(latest["Close"], "item") else latest["Close"]
    ma50 = latest["ma50"].item() if hasattr(latest["ma50"], "item") else latest["ma50"]
    ma200 = latest["ma200"].item() if hasattr(latest["ma200"], "item") else latest["ma200"]

    # Apply rules
    if rsi < 30 and close > ma50:
        decision = "BUY"
    elif rsi > 70 or close < ma200:
        decision = "SELL"
    else:
        decision = "HOLD"

    text = f"{ticker}: {decision} (RSI={rsi:.2f}, Price={close:.2f})"
    data = {
        "Ticker": ticker,
        "Decision": decision,
        "RSI": round(rsi, 2),
        "Price": round(close, 2),
        "MA50": round(ma50, 2),
        "MA200": round(ma200, 2),
        "Date": datetime.today().strftime("%Y-%m-%d")
    }

    return text, data

# ------------------ List of tickers ------------------
# Read tickers from text file
with open("stocks.txt", "r") as f:
    tickers = [line.strip() for line in f if line.strip()]
results = []
messages_to_send = []

# ------------------ Check stocks ------------------
for ticker in tickers:
    text, data = check_stock(ticker)
    print(text)
    if data:
        results.append(data)
        if data["Decision"] in ["BUY", "SELL"]:
            messages_to_send.append(text)

# ------------------ Save CSV ------------------
df_results = pd.DataFrame(results)
df_results.to_csv("stock_report.csv", index=False)

# ------------------ Send email if needed ------------------
if messages_to_send and EMAIL_USER and EMAIL_PASS and EMAIL_TO:
    subject = "Stock Action Alert"
    body = "The following stocks have BUY/SELL signals:\n\n" + "\n".join(messages_to_send)

    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

    print("Email sent!")
else:
    print("No action needed today or email settings missing.")





