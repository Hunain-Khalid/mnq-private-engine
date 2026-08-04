# 📜 ALPHA FLUSH NODE - CHANGELOG

All notable changes, architectural pivots, and engineering milestones to this project will be documented in this file.

## [Unreleased]
### Added
- Architecture diagram and end-to-end workflow documentation (`architecture.md`).
- Master structural blueprint for DuckDB + Parquet + FastAPI + React stack.

## [0.2.0] - 2026-07-31 (The Quant DevOps Pivot)
### Added
- Local WSL2 + Docker CLI integration for containerized execution.
- High-speed `DatabentoRTHDataReader` memory-stream parser for raw `.zst.csv` files.
- Strict Regular Trading Hours (RTH) timezone filtering (Eastern Time / NYC).

### Changed
- **Pivoted Stack:** Abandoned monolithic QuantConnect LEAN open-source engine wrappers to eradicate C#/Python type-casting bugs and thread-timeout issues.
- Migrated to an elite, decoupled Research-to-Production layout (DuckDB, Parquet, VectorBT, FastAPI, React).

## [0.1.0] - 2026-07-30 (The Inception)
### Added
- Initial migration of discretionary TradingView Pine Script strategy into Python.
- Secure local configuration layer (`config.json`) via Dependency Injection.
- Setup of private GitHub repository and secure `.gitignore` firewall.