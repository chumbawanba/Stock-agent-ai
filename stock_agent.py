import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from langchain.agents import Tool, initialize_agent
from langchain_huggingface import HuggingFacePipeline
from transformers import pipeline

# ------------------ Tool Function ------------------
def check_stock(ticker: str) -> str:
    df = yf.download(ticker, period="6mo", interval="1d", auto_adjust=True)
    if df.empty:
        return f"{ticker}: No data found."

    close_series = df["Close"].squeeze()
    df["rsi"] = RSIIndicator(close_series).rsi().squeeze()
    df["ma50"] = df["Close"].rolling(window=50).mean()
    df["ma200"] = df["Close"].rolling(window=200).mean()
    latest = df.iloc[-1]

    # Convert to scalars
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

# ------------------ Define Tool ------------------
tools = [
    Tool.from_function(
        func=check_stock,
        name="check_stock",
        description="Checks stock indicators (RSI, MA50, MA200) and returns Buy/Sell/Hold."
    )
]

# ------------------ Hugging Face LLM ------------------
# CPU-friendly causal LM (~1.5GB quantized)
pipe = pipeline(
    "text-generation",
    model="TheBloke/Llama-2-7b-GPTQ",
    max_new_tokens=128,
    device=-1
)
llm = HuggingFacePipeline(pipeline=pipe)

# ------------------ Initialize Agent ------------------
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent_type="zero-shot-react-description",
    handle_parsing_errors=True
)

# ------------------ Stocks to Evaluate ------------------
tickers = ["AAPL", "TSLA", "NVDA", "GOOGL", "MSFT"]

# ------------------ Run Agent ------------------
for ticker in tickers:
    result = agent.invoke(f"Check if {ticker} is a good investment using the check_stock tool.")
    print(result)



