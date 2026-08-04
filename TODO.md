# 📋 ALPHA FLUSH NODE - MASTER TODO LIST

## Phase 1: Data Infrastructure & Storage (Current)
- [ ] **Task 1.1:** Finalize the DuckDB + Parquet local storage directory (`/storage/`).
- [ ] **Task 1.2:** Write the master ETL script to convert raw Databento `.zst` files into compressed `.parquet` files.
- [ ] **Task 1.3:** Verify in-memory SQL query speeds on 16 years of $NQ data using DuckDB.

## Phase 2: Quantitative Research & Optimization
- [ ] **Task 2.1:** Initialize the local Jupyter Lab environment (`/research/`).
- [ ] **Task 2.2:** Translate V2.5.3 Pine Script strategy logic (HMA slopes, VWAP bands, exhaustion peaks) into vectorized Python code.
- [ ] **Task 2.3:** Build a VectorBT parameter optimization script to find the "stability corridor" for ATR multipliers.

## Phase 3: Production Backend & Execution Engine
- [ ] **Task 3.1:** Initialize the FastAPI backend server (`/backend/app/`).
- [ ] **Task 3.2:** Implement the **IP Firewall** (`/secret_sauce/`) and the dynamic try/except fallback loading loop.
- [ ] **Task 3.3:** Integrate the live paper execution loop (hooking into a broker API like Alpaca or IBKR).

## Phase 4: Recruiter Frontend & GitHub Pages Deployment
- [ ] **Task 4.1:** Scaffold the React (Next.js) frontend dashboard (`/frontend/`).
- [ ] **Task 4.2:** Integrate TradingView's `lightweight-charts` to render real-time equity curves and drawdown metrics.
- [ ] **Task 4.3:** Deploy the static frontend build to **GitHub Pages** as your live portfolio billboard.