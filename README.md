# Stock-agent-ai
# Stock Agent AI - Rules-Based Alerts

This repository contains a **Python stock agent** that checks a list of stocks and generates **Buy/Sell/Hold signals** based on simple technical indicators:

- **RSI** (Relative Strength Index)
- **MA50** (50-day Moving Average)
- **MA200** (200-day Moving Average)

It sends **HTML email alerts** only for Buy/Sell signals and saves a **CSV report**. Stock tickers are read from a `stocks.txt` file in the repository.

---

## Features

- Read tickers dynamically from `stocks.txt`
- Apply simple technical rules to determine Buy/Sell/Hold
- Save CSV report (`stock_report.csv`) of all stocks
- Send HTML email alert with a table of actionable stocks
- Each ticker in the email links to its Yahoo Finance page
- Fully automated via **GitHub Actions**

---

## Setup

### 1. Stock List

Create a file `stocks.txt` in the root of the repo:

AAPL
TSLA
NVDA
GOOGL
MSFT

yaml
Copy code

Add as many tickers as you want, one per line.

---

### 2. Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
requirements.txt contains:

nginx
Copy code
yfinance
pandas
ta
3. GitHub Secrets for Email
Create the following secrets in your GitHub repository:

EMAIL_USER → Your email address (Gmail works)

EMAIL_PASS → Your app password or email password

EMAIL_TO → Destination email address

Important: For Gmail, you must create an App Password if 2FA is enabled.

GitHub Actions Workflow
The agent can run automatically every day using GitHub Actions. Example workflow .github/workflows/run-stock-agent.yml:

yaml
Copy code
name: Run Stock Agent

on:
  schedule:
    - cron: '0 14 * * *'  # Runs daily at 14:00 UTC
  workflow_dispatch:

jobs:
  run-agent:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Stock Agent
        env:
          EMAIL_USER: ${{ secrets.EMAIL_USER }}
          EMAIL_PASS: ${{ secrets.EMAIL_PASS }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
        run: python stock_agent.py

      - name: Upload CSV as artifact
        uses: actions/upload-artifact@v4
        with:
          name: stock-report
          path: stock_report.csv
How it Works
Reads tickers from stocks.txt

Downloads 6 months of daily stock data using yfinance

Calculates:

RSI

50-day moving average

200-day moving average

Applies simple rules:

Buy if RSI < 30 and price > MA50

Sell if RSI > 70 or price < MA200

Otherwise Hold

Prints all results in the GitHub Actions log

Sends HTML email if any stock is Buy or Sell

Saves a CSV file as an artifact in GitHub Actions

Email Output
Only sends email if there is Buy/Sell signal

HTML table includes clickable links to Yahoo Finance pages

License
This project is open source under the MIT License.

yaml
Copy code
