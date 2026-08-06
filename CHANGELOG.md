# 📜 Alpha Flush Node - Engineering Changelog

All notable changes, infrastructure pivots, and architectural milestones for this project will be documented in this file.

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