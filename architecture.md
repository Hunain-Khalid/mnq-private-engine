╔════════════════════════════════════════════════════════════════════════════════════╗
 ║                         🔒 PRIVATE LOCAL HARD DRIVE                                ║
 ╚════════════════════════════════════════════════════════════════════════════════════╝
 
  [Raw Databento .zst / .csv]
               │
               ▼  (ETL Script: Stream & Downsample)
   ┌───────────────────────┐
   │  DuckDB + Parquet     │ ◄─── (In-Memory SQL Analytical Storage Tier)
   └───────────────────────┘
         │               ▲
         │ (SQL Query)   │ (Log Performance / Retrain Feedback Loop)
         ▼               │
   ┌─────────────────────┴────────┐
   │ Jupyter Research Lab         │ ◄─── (Alpha Prototyping & EDA)
   └──────────────┬───────────────┘
                  │
                  ▼ (Pass Strategy Matrix)
   ┌──────────────────────────────┐
   │ VectorBT Pro Optimization    │ ──(Iterative Grid/Bayesian Search)──┐
   └──────────────┬───────────────┘                                     │
                  │                                                     │
                  ▼ (Find Stability Corridors)                          │
   ┌──────────────────────────────┐                                     │
   │ /backend/app/secret_sauce/   │ ◄─── 🔒 PRIVATE IP (Firewalled)     │
   └──────────────┬───────────────┘                                     │
                  │                                                     │
                  ▼ (Dynamic Try/Except Injection)                      │
   ┌──────────────────────────────┐                                     │
   │ FastAPI Execution Backend    │ ◄─── Risk Engine & Live Paper Node  │
   └──────────────┬───────────────┘                                     │
                  │                                                     │
                  ├──(Execute Paper Trades via Broker API)──────────────┤
                  │                                                     │
                  ▼ (JSON Telemetry REST API)                           │
 ╔════════════════════════════════════════════════════════════════════════════════════╗
 ║                         🌐 PUBLIC INTERNET / RECRUITERS                            ║
 ╚════════════════════════════════════════════════════════════════════════════════════╝
                  │                                                     │
                  ▼                                                     │
   ┌──────────────────────────────┐                                     │
   │ React / Next.js Dashboard    │ ◄─── TradingView Lightweight Charts │
   └──────────────┬───────────────┘                                     │
                  │                                                     │
                  ▼ (Static Deployment)                                 │
   ┌──────────────────────────────┐                                     │
   │ GitHub Pages (Live Node)     │ ◄─── Recruiter Showcase Billboard   │
   └──────────────────────────────┘                                     │
                  │                                                     │
                  └──────(Export Trade Logs / CSVs)─────────────────────┘