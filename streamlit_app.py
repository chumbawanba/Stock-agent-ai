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
        start = end - dat

