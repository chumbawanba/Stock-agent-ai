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

# ------------------ Read tickers from stocks.txt ------------------
try:
    with open("stocks.txt", "r") as f:
        tickers = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("stocks.txt file not found!")
    tickers = []

# ------------------ Stock rules function ------------------
def check_stock(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d")

        # ✅ Ensure Close is 1D (some tickers like BRK-B return 2D arrays)
        df["Close"] = df["Close"].squeeze()

        # Compute indicators
        df["rsi"] = RSIIndicator(df["Close"]).rsi()
        df["ma50"] = df["Close"].rolling(window=50).mean()
        df["ma200"] = df["Close"].rolling(window=200).mean()

        latest = df.iloc[-1]

        action = "Hold"
        reason = "No clear signal."
        potential_return = 0

        if latest["rsi"] < 30 and latest["Close"] > latest["ma50"]:
            action = "Buy"
            reason = "RSI is low and price is above MA50 — potential uptrend."
            potential_return = ((latest["ma200"] - latest["Close"]) / latest["Close"]) * 100
        elif latest["rsi"] > 70 and latest["Close"] < latest["ma50"]:
            action = "Sell"
            reason = "RSI is high and price fell below MA50 — potential downtrend."
            potential_return = ((latest["Close"] - latest["ma200"]) / latest["Close"]) * 100

        return {
            "Symbol": ticker,
            "Action": action,
            "Reason": reason,
            "Potential Return (%)": round(potential_return, 2)
        }

    except Exception as e:
        return {
            "Symbol": ticker,
            "Action": "Error",
            "Reason": f"Error analyzing {ticker}: {str(e)}",
            "Potential Return (%)": 0
        }

# ------------------ Check stocks ------------------
results = []
messages_to_send = []

for ticker in tickers:
    text, data = check_stock(ticker)
    print(text)
    if data:
        results.append(data)
        if data["Decision"] in ["BUY", "SELL"]:
            messages_to_send.append(data)  # store full data for table

# ------------------ Save CSV ------------------
df_results = pd.DataFrame(results)
df_results.to_csv("stock_report.csv", index=False)

# ------------------ Send HTML email if needed ------------------
if messages_to_send and EMAIL_USER and EMAIL_PASS and EMAIL_TO:
    subject = "Stock Action Alert"
    
    # Create HTML table
    html_table = "<table border='1' cellpadding='5' cellspacing='0'>"
    html_table += "<tr><th>Ticker</th><th>Decision</th><th>RSI</th><th>Price</th><th>MA50</th><th>MA200</th><th>Date</th></tr>"
    for stock in messages_to_send:
        html_table += f"<tr><td>{stock['Ticker']}</td><td>{stock['Decision']}</td><td>{stock['RSI']}</td><td>{stock['Price']}</td><td>{stock['MA50']}</td><td>{stock['MA200']}</td><td>{stock['Date']}</td></tr>"
    html_table += "</table>"

    body = f"<h3>The following stocks have BUY/SELL signals:</h3>{html_table}"

    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

    print("Email sent with HTML table!")
else:
    print("No action needed today or email settings missing.")






