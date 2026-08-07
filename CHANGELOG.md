#  Alpha Flush Node - Master Engineering & Research Changelog

All system architecture pivots, UI upgrades, and chronological quantitative research hypotheses are logged below.

---

##  Quantitative Research Ledger (Alpha Experiments)

### [v1.0.0-ALPHA] - 2026-08-06 14:30 EST (Active Experiment)
- **Target Asset:** MNQ (Nasdaq E-mini Micro Futures)
- **Core Hypothesis:** Implementing a Hull Moving Average (HMA) multi-timeframe slope filter combined with an Average True Range (ATR) expansion gate will filter out low-volume regular trading hours (RTH) chop. 
- **Expected Outcome:** Lower overall trade frequency by ~40%, but significantly reduce maximum drawdown and push the Out-of-Sample (OOS) Sharpe ratio above 1.5.

### [v0.1.0-BASELINE] - 2026-08-05 21:00 EST (Archived Experiment)
- **Phase:** In-Sample Training (IS) [FAILED]
- **Key Metrics Recorded:** Sharpe: -0.28 | Max Drawdown: 31.7% ($373,525) | Win Rate: 44.6% (520 Trades) | Profit Factor: 0.977
- **Root Cause Analysis:** Naive Moving Average crossover suffered from severe over-trading during chop, resulting in negative expectancy.
- **Pivot Action:** Abandon SMA logic. Proceed to v1.0 HMA + ATR volatility gating.

---

##  System Architecture & Infrastructure Changelog

## [v2.1.0] - 2026-08-06 (The Modular Architecture Refactor)
### Added
- **Strategy Leaderboard & Comparison Engine:** Added an automated ranking table sorting all backtests by Sharpe Ratio, complete with a Reigning Champion vs. Challenger Delta metric.
- **Dotted Baseline Rules:** Integrated the $1,000,000 starting capital reference line across all equity charts (Hero, Iterations, and Live Paper Trading).
- **Pro Quant Suite Tabs:** Restructured iteration cards into 4 distinct tabs (`Equity Curve & Summary`, `Trade Analytics`, `Changelog`, and `Raw CSV Inspector`) to eliminate UI crowding.

### Changed
- **Codebase Modularization:** Refactored the monolithic `app.py` script into clean, professional backend metrics (`backend_metrics.py`) and UI component (`ui_components.py`) modules.
- **Restored PDF Artifact Downloads:** Re-anchored full PDF report download buttons inside the changelog tabs with dynamic file size tracking.

---

## [v2.0.0] - 2026-08-06 (The Cloud & Portfolio Pivot)
### Added
- **Streamlit Research Gallery (`app.py`):** Built a zero-maintenance, multi-page portfolio web app with `@st.cache_data` performance optimizations.
- **Dynamic Artifact Rendering:** Integrated automated fuzzy-matching for QuantConnect nested JSON metrics and multi-point equity curves calculated from raw trade CSV execution logs.
- **Conditional Altair Visuals:** Upgraded equity curves to professional area charts with dynamic green/red gain/drawdown coloring and real timeline date axes.
- **Phase & Status Badging:** Added automated parsing for In-Sample (IS) and Out-of-Sample (OOS) validation tags.

### Changed
- **Infrastructure Shift:** Migrated from local Docker/WSL2/DuckDB data pipelines to QuantConnect's fully managed cloud LEAN Python environment, eliminating custom data-routing friction.
- **Artifact Compression:** Developed a Universal Artifact Compressor (`compress_reports.py`) utilizing Ghostscript for PDFs and JSON whitespace minification.

---

## [v1.0.0] - 2026-08-01 (The Local Infrastructure Phase)
### Added
- Initial setup of QuantConnect LEAN local engine inside Docker via WSL2.
- Master ETL pipeline (`etl_pipeline.py`) for raw Databento `.zst` futures ingestion.
- Pre-computed Multi-Resolution Pyramids inside DuckDB for regular trading hours (RTH).
- Data Integrity Test Suite (`validate_data.py`) verifying chronological sorting and zero OHLC gaps.

### Pivot Notice
- Deprecated local C#/Python type-casting and Zstd memory stream parsing in favor of QuantConnect's cloud data library for faster alpha iteration.