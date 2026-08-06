# 🏛️ Alpha Flush Node
**Systematic Nasdaq Futures (MNQ) Trend-Following & Volatility-Gated Quantitative Engine**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![QuantConnect LEAN](https://img.shields.io/badge/Engine-QuantConnect-orange.svg)](https://www.quantconnect.com/)
[![Streamlit App](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)

---

## 🎯 Core Objective
Rebuild a discretionary TradingView MNQ trend-following flush strategy into a rigorous, systematic quantitative engine to eliminate emotional drawdowns and enforce strict programmatic risk controls.

## 📊 Strategy Logic & Rules
- **Trend Filter:** Hull Moving Average (HMA) multi-timeframe slope tracking.
- **Volatility Gate:** Average True Range (ATR) expansion filter to avoid low-volume RTH chop.
- **Risk Management:** Dynamic 2x ATR position sizing and strict portfolio drawdown constraints.

## 🏛️ Project Architecture
- **Research & Execution:** QuantConnect Cloud (Python/LEAN Engine).
- **Validation Pipeline:** In-Sample (IS) optimization vs. blind Out-of-Sample (OOS) verification.
- **Artifact Tracking:** Automated compression of QuantConnect PDF tear sheets, minified JSON metrics, and CSV execution logs.
- **Portfolio Frontend:** Zero-maintenance Streamlit Strategy Gallery rendering interactive equity curves and raw audit tables.

## 🚀 Local Development & Execution
1. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt

## Launch the Streamlit Strategy Gallery locally:
streamlit run app.py