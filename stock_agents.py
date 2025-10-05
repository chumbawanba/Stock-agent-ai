from langchain.tools import tool
from langchain.agents import initialize_agent, Tool
from langchain.llms.fake import FakeListLLM
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

@tool
def check_stock(ticker: str) -> str:
    """Check stock using RSI and moving averages. Returns Buy/Sell/Hold decision."""
    df = yf.download(ticker, period="6mo", interval="1d")
    if df.empty:
        return f"{ticker}: No data found."

    df["rsi"] = RSIIndicator(df["Close"]).rsi()
    df["ma50"] = df["Close"].rolling(window=50).mean()
    df["ma200"] = df["Close"].rolling(window=200).mean()

    latest = df.iloc[-1]
    
    decision = "HOLD"
    if latest["rsi"] < 30 and latest["Close"] > latest["ma50"]:
        decision = "BUY"
    elif latest["rsi"] > 70 or latest["Close"] < latest["ma200"]:
        decision = "SELL"

    return f"{ticker}: {decision} (RSI={latest['rsi']:.2f}, Price={latest['Close']:.2f})"

# Set up LangChain agent
llm = FakeListLLM(responses=[""])
tools = [Tool.from_function(check_stock)]
agent = initialize_agent(tools, llm, agent_type="zero-shot-react-description")

# List of stocks to evaluate
tickers = ["AAPL", "TSLA", "NVDA", "GOOGL", "MSFT"]

# Run agent on each
for ticker in tickers:
    result = agent.run(f"Check if {ticker} is a good investment using the check_stock tool.")
    print(result)
