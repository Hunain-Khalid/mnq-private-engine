#  Alpha Flush Node - Master Engineering & Research Changelog

All system architecture pivots, UI upgrades, and chronological quantitative research hypotheses are logged below.

---

### [v0.1.01-EOD] - 2026-08-07 15:00 EST (Archived Experiment)
- **In-Sample Window:** 2020-01-01 to 2024-06-30 (Parameter Tuning)
- **Out-of-Sample Window:** 2024-07-01 to 2026-06-30 (Blind Verification)
- **Target Asset:** SP_500_E_MINI (ES)
- **Pre-Execution Hypothesis:** Forcing an absolute End-of-Day liquidation between 3:45-3:49 PM EST to avoid overnight gaps will **substantially degrade performance**.
- **Economic Rationale:** Trend-following models rely on multi-day momentum and overnight gap expansions. Forcing flat closes amputates fat-tail returns and increases cumulative intraday execution friction.
- **Empirical Audit Results:**
  - **In-Sample (Training):** Sharpe: 0.1 | CAGR: 4.1% | Max Drawdown: 15.1%
  - **Out-of-Sample (Blind Test):** Sharpe: -0.8 | CAGR: -4.9% | Max Drawdown: 17.1%
- **Post-Mortem Conclusion:** **Hypothesis Proven Correct.** Cutting positions flat every afternoon completely destroyed trend-following alpha. EOD liquidation rule abandoned.
**Strategic Pivot for Prop Firm Compliance:** For live prop firm evaluations (Apex/Topstep), sacrificing some raw momentum via EOD flattening is an acceptable trade-off to survive brutal trailing max drawdown rules and overnight gap risk.

### [v0.1.0-BASELINE] - 2026-08-05 21:00 EST (Archived Experiment)
- **Phase:** In-Sample Training (IS) [FAILED]
- **Key Metrics Recorded:** Sharpe: -0.28 | Max Drawdown: 31.7% ($373,525) | Win Rate: 44.6% (520 Trades) | Profit Factor: 0.977
- **Root Cause Analysis:** Naive Moving Average crossover suffered from severe over-trading during chop, resulting in negative expectancy.
- **Pivot Action:** Abandon SMA logic. Proceed to v1.0 HMA + ATR volatility gating.

---

##  System Architecture & Infrastructure Changelog

## [v2.7.0] - 2026-08-08 (The Advanced Tail-Risk & Spaghetti Variance Update)
### Added
- **Extended Monte Carlo Tail Bounds (P5 & P95):** Upgraded the bootstrap simulation engine to map extreme tail risk (P5 deep red and P95 vivid green) alongside P10, Median, and P90 confidence boundaries.
- **Spaghetti Variance Overlay (`ui_components.py`):** Added 70 semi-transparent individual equity trajectory paths rendered in the background of the Monte Carlo chart to visually capture trade sequence path dependency.
- **Drawdown Distribution Histogram:** Integrated a secondary frequency histogram positioned directly underneath the Monte Carlo equity chart, tracking max drawdowns across all simulations to evaluate prop-firm risk limits.

### Optimized
- **Monte Carlo Opacity & Contrast:** Fine-tuned spaghetti path opacity (`0.5`) and confidence band stroke weight (`2.2px` at `0.85` opacity) for optimal Bloomberg-style terminal readability.
- **Tail-Risk Metric Cards:** Extended the dynamic red/green institutional metric styling to Monte Carlo summary outputs (Projected Median Ending PnL and Risk of Ruin).

## [v2.6.0] - 2026-08-08 (The Institutional Terminal UI & Dynamic Risk Polish)
### Added
- **4x5 Institutional Quant Grid (20 Metrics):** Expanded the risk metric matrix to 20 core institutional metrics, incorporating System Quality Number (SQN), Ulcer Index, Trade Expectancy ($), MAE/MFE averages, and granular win/loss breakdowns.
- **Dynamic Institutional Metric Cards (`ui_components.py`):** Replaced default Streamlit cards with custom HTML/CSS institutional containers featuring conditional red/green states (crimson red `#2A1215` with `#FF5252` borders for negative returns, drawdowns, and high risk of ruin; glowing green for positive performance).
- **Outlined Chart Containers:** Wrapped all Altair charts (Equity curves, Monte Carlo confidence bands, Trade Distribution donuts, and PnL histograms) in clean institutional grey/white outlined containers.
- **Crisp Institutional Dividers:** Replaced default UI dividers with sleek white-to-slate-grey gradient horizontal rules (`#E2E8F0` to `#1E293B`).

### Optimized
- **Fragmented Monte Carlo Engine (`@st.fragment`):** Isolated the Monte Carlo simulation sliders and charts so parameter adjustments (simulations up to 10k, horizons up to 500) execute instantly in RAM without triggering a full-page Streamlit reload.
- **Modularized UI Styling Architecture:** Extracted global CSS and terminal themes into a dedicated `ui_styles.py` module to maintain strict Separation of Concerns across the app architecture.
- **Memory & Rendering Hygiene:** Enforced `low_memory=False` and optimized data downcasting for large historical trade and order CSV logs to prevent browser DOM lag.

## [v2.5.1] - 2026-08-07 (The Pro Dashboard & ISO Compliance Polish)
### Added
- **Dynamic Hero Date Ranges:** Automatically extracts and displays the exact temporal boundaries (`YYYY-MM-DD` start/end dates) directly in the reigning champion equity chart header.

### Fixed
- **Robust Drawdown Percentage Normalization (`backend_metrics.py`):** Added dynamic type-checking to convert raw QuantConnect decimal drawdowns (e.g., `0.317`) into pristine percentage strings (`31.7%`) across all metric cards.
- **Strict Artifact Scoping:** Finalized backend fuzzy-matching to guarantee zero cross-contamination of equity curves and CSV logs between different model iterations.

---

## [v2.5.0] - 2026-08-07 (Cloud Deployment & Robust File Scoping)
### Added
- **ISO Date Formatting on Altair Charts:** Standardized equity curve tooltips and timelines to clean `YYYY-MM-DD` ISO formatting.
- **Granular PnL Buckets:** Upgraded trade returns distribution histograms to render higher-resolution binning for deep-dive performance analysis.

### Fixed
- **Cloud Git Tracking & Fuzzy-Matching:** Removed `reports/` from `.gitignore` and upgraded file-locator loops with strict fuzzy-matching to ensure 100% artifact synchronization between local environments and Streamlit Community Cloud.

---

## [v2.4.0] - 2026-08-07 (The Card-Swiper & Pro Quant Suite)
### Added
- **React-Like Card-Swiper Carousel (`app.py`):** Replaced vertical card stacking with a session-state-powered card deck featuring smooth `< Prev` and `Next >` arrow navigation to flip between In-Sample training and Out-of-Sample blind tests.
- **Automated IS Lineage Stacking:** Configured iteration badges to dynamically preserve and display In-Sample training results alongside Out-of-Sample validation states.
- **Enhanced Quantitative Metrics:** Added Sortino Ratio, Trade Expectancy ($ per trade), Recovery Factor, and Payoff Ratios to the 12-metric institutional quant grid.

---

## [v2.3.0] - 2026-08-07 (The Pro Quant Suite & UI Polish)
### Added
- **Sortino & Payoff Ratio Engine:** Integrated downside-deviation risk calculations and trade Payoff Ratios into the metrics suite.
- **Dynamic 12-Metric Grid:** Upgraded Streamlit UI cards into an institutional 3-row layout with custom CSS typography scaling and inline percentage breakdowns (Avg Win/Loss % and Max Drawdown dollar scale).
- **Starting Capital Baselines:** Anchored all Altair equity charts with a $1,000,000 orange dashed starting capital rule.

### Changed
- **Streamlined Visuals:** Removed jarring multi-color line switches in favor of a clean, razor-sharp institutional green equity line.
- **Component Scoping:** Fixed strict file-stem scoping in `backend_metrics.py` to prevent multi-iteration equity curve cross-contamination.

---

## [v2.2.0] - 2026-08-06 (The Pro Quant Suite Upgrade)
### Added
- **Sortino Ratio Engine:** Implemented downside-deviation risk-adjusted return calculations alongside Sharpe Ratio, providing a fairer evaluation of trend-following outlier gains.
- **Advanced Execution Metrics:** Added automated calculation for Trade Expectancy ($ per trade) and Recovery Factor (Net Profit / Max Drawdown).
- **Institutional 12-Metric Grid:** Upgraded Streamlit UI metric cards into a 3-row pro grid featuring CSS-scaled typography and inline percentage breakdowns.

---

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