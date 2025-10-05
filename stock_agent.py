import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ------------------ Email settings ------------------
SMTP_SERVER = "smtp.gmail.com"  # Example: Gmail SMTP
SMTP_PORT = 587
EMAIL_USER = "your_email@gmail.com"
EMAIL_PASS = "your_app_password"  # Use App Password, not your main Gmail password
EMAIL_TO = "recipient_email@gmail.com"

# ------------------ Stock rules function ------------------
def check_stock(ticker: str):
    df = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True)
    if df.empty:
        return f"{ticker}: No data found.", None

    close_series = df["Close"]
    if isinstance(close_series, pd.DataFrame):
        close_series = close_series.squeeze()  # Flatten 2D to 1D

    df["rsi"] = RSIIndicator(close_series).rsi()
    df["ma50"] = df["Close"].rolling(window=50).mean()
    df["ma200"] = df["Close"].rolling(window=200).mean()

    latest = df.iloc[-1]
    rsi = latest["rsi"]
    close = latest["Close"]
    ma50 = latest["ma50"]
    ma200 = latest["ma200"]

    if rsi < 30 and close > ma50:
        decision = "BUY"
    elif rsi > 70 or close < ma200:
        decision = "SELL"
    else:
        decision = "HOLD"

    text = f"{ticker}: {decision} (RSI={rsi:.2f}, Price={close:.2f})"
    data = {"Ticker": ticker, "Decision": decision, "RSI": rsi, "Price": close,
            "MA50": ma50, "MA200": ma200, "Date": datetime.today().strftime("%Y-%m-%d")}

    return text, data


# ------------------ List of tickers ------------------
tickers = ["AAPL", "TSLA", "NVDA", "GOOGL", "MSFT"]
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
if messages_to_send:
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
    print("No action needed today.")




