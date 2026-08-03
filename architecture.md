╔════════════════════════════════════════════════════════════════════════════════════╗
 ║                         🔒 PRIVATE LOCAL HARD DRIVE                                ║
 ╚════════════════════════════════════════════════════════════════════════════════════╝
 
  [Raw Databento .zst / .csv]
               │
               ▼  (ETL Script: Stream & Downsample)
   ┌───────────────────────┐
   │  DuckDB + Parquet     │ ◄─── (Lightning-Fast In-Memory SQL Query Layer)
   └───────────────────────┘
         │               │
         │ (Query)       │ (Query)
         ▼               ▼
   ┌───────────┐   ┌──────────────────────────────┐
   │ Jupyter   │   │  VectorBT Pro Optimization   │
   │ Research  │   │  (Vectorized Grid Searches)  │
   └───────────┘   └──────────────┬───────────────┘
                                  │
                                  ▼ (Extract Winning Parameters)
                   ┌──────────────────────────────┐
                   │  /backend/app/secret_sauce/  │ ◄─── 🔒 PRIVATE IP (Firewalled)
                   └──────────────┬───────────────┘
                                  │
                                  ▼ (Dynamic Try/Except Injection)
                   ┌──────────────────────────────┐
                   │  FastAPI Execution Backend   │ ◄─── Risk Engine & Paper Node
                   └──────────────┬───────────────┘
                                  │
                                  ▼ (JSON Telemetry REST API)
 ╔════════════════════════════════════════════════════════════════════════════════════╗
 ║                         🌐 PUBLIC INTERNET / RECRUITERS                            ║
 ╚════════════════════════════════════════════════════════════════════════════════════╝
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │  React / Next.js Dashboard   │ ◄─── TradingView Lightweight Charts
                   └──────────────┬───────────────┘
                                  │
                                  ▼ (Static Deployment)
                   ┌──────────────────────────────┐
                   │   GitHub Pages (Live Node)   │ ◄─── Recruiter Showcase Billboard
                   └──────────────────────────────┘