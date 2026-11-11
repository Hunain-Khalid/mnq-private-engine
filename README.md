# Alpha Flush Node
**Systematic Nasdaq Futures (MNQ) Trend-Following & Volatility-Gated Quantitative Engine**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![QuantConnect LEAN](https://img.shields.io/badge/Engine-QuantConnect-orange.svg)](https://www.quantconnect.com/)
[![Streamlit App](https://img.shields.io/badge/UI-Streamlit-red.svg)](https://streamlit.io/)

---

## UI Gallery
<img width="1530" height="826" alt="Screenshot 2026-11-09 103054" src="https://github.com/user-attachments/assets/20463559-d4ad-475f-aceb-26b65e6f5024" />
<img width="1481" height="838" alt="Screenshot 2026-11-09 103108" src="https://github.com/user-attachments/assets/33261efb-13f3-4b22-be10-8c106c840a05" />
<img width="1479" height="836" alt="Screenshot 2026-11-09 103124" src="https://github.com/user-attachments/assets/29b41a6d-c88c-40b3-add2-1317f429c1d6" />
<img width="1511" height="600" alt="Screenshot 2026-11-09 103135" src="https://github.com/user-attachments/assets/c0695a6d-2e91-4a35-8225-fa1d5749c6ba" />
<img width="1487" height="730" alt="Screenshot 2026-11-09 103203" src="https://github.com/user-attachments/assets/ce87b7e6-3df0-495c-8097-0f6395799038" />
<img width="1481" height="297" alt="Screenshot 2026-11-09 103210" src="https://github.com/user-attachments/assets/9ffe8212-ad4c-405c-a83b-d70019dde36e" />
<img width="1484" height="655" alt="Screenshot 2026-11-09 103031" src="https://github.com/user-attachments/assets/a7e2f965-9c7c-4e1f-96d4-f3089b756e3a" />
<img width="1487" height="799" alt="Screenshot 2026-11-09 103041" src="https://github.com/user-attachments/assets/b4752c4e-b9a4-4a69-9951-051f90b58110" />

## Core Objective
Rebuild a discretionary TradingView MNQ trend-following flush strategy into a rigorous, systematic quantitative engine to eliminate emotional drawdowns and enforce strict programmatic risk controls.

## Strategy Logic & Rules
- **Trend Filter:** Hull Moving Average (HMA) multi-timeframe slope tracking.
- **Volatility Gate:** Average True Range (ATR) expansion filter to avoid low-volume RTH chop.
- **Risk Management:** Dynamic 2x ATR position sizing and strict portfolio drawdown constraints.

## Project Architecture
- **Research & Execution:** QuantConnect Cloud (Python/LEAN Engine).
- **Validation Pipeline:** In-Sample (IS) optimization vs. blind Out-of-Sample (OOS) verification.
- **Artifact Tracking:** Automated compression of QuantConnect PDF tear sheets, minified JSON metrics, and CSV execution logs.
- **Portfolio Frontend:** Zero-maintenance Streamlit Strategy Gallery rendering interactive equity curves and raw audit tables.

## Local Development & Execution
1. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt

## Launch the Streamlit Strategy Gallery locally:
streamlit run app.py
