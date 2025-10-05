from langchain.agents import Tool, initialize_agent
from langchain_community.llms.fake import FakeListLLM
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

# Tool logic
def check_stock(ticker: str) -> str:
    df = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True)
    if df.empty:
        return f"{ticker}: No data found."

    # Ensure Close is 1D
    close_series = df["Close"].squeeze()
    df["rsi"] = RSIIndicator(close_series).rsi().squeeze()

    # Moving averages
    df["ma50"] = df["Close"].rolling(window=50).mean()
    df["ma200"] = df["Close"].rolling(window=200).mean()

    latest = df.iloc[-1]

    # Convert any 1-element Series to scalar
    rsi = latest["rsi"].item() if isinstance(latest["rsi"], pd.Series) else latest["rsi"]
    close = latest["Close"].item() if isinstance(latest["Close"], pd.Series) else latest["Close"]
    ma50 = latest["ma50"].item() if isinstance(latest["ma50"], pd.Series) else latest["ma50"]
    ma200 = latest["ma200"].item() if isinstance(latest["ma200"], pd.Series) else latest["ma200"]

    decision = "HOLD"
    if rsi < 30 and close > ma50:
        decision = "BUY"
    elif rsi > 70 or close < ma200:
        decision = "SELL"

    return f"{ticker}: {decision} (RSI={rsi:.2f}, Price={close:.2f})"




# Tool setup
tools = [
    Tool.from_function(
        func=check_stock,
        name="check_stock",
        description="Checks stock indicators and returns a Buy/Sell/Hold decision"
    )
]

# Dummy LLM output that calls the tool directly
fake_llm = FakeListLLM(
    responses=[
        "Action: check_stock\nAction Input: \"AAPL\"",
        "Action: check_stock\nAction Input: \"TSLA\"",
        "Action: check_stock\nAction Input: \"NVDA\"",
        "Action: check_stock\nAction Input: \"GOOGL\"",
        "Action: check_stock\nAction Input: \"MSFT\""
    ]
)

# Initialize agent
agent = initialize_agent(
    tools,
    llm=fake_llm,
    agent_type="zero-shot-react-description",
    handle_parsing_errors=True  # Optional but helpful in dev
)

# Run agent for multiple tickers
tickers = ["AAPL", "TSLA", "NVDA", "GOOGL", "MSFT"]
for ticker in tickers:
    result = agent.invoke(f"Check if {ticker} is a good investment using the check_stock tool.")
    print(result)

