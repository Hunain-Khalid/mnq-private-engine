alpha_flush_node/
├── .gitignore                     <-- Add "storage/" and "backend/app/secret_sauce/" here!
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                <-- Open Source FastAPI Router & Paper Order Loops
│   │   ├── database.py            <-- Open Source DuckDB Query Managers
│   │   │
│   │   └── secret_sauce/          <-- 🔒 LOCKED: PROPRIETARY IP (NEVER UPLOADED)
│   │       ├── __init__.py
│   │       ├── alpha_signals.py   <-- Your secret math indicators & trigger thresholds
│   │       └── execution_keys.env <-- Your live Alpaca / Databento paid API secret keys
│   │
│   ├── requirements.txt
│   └── run.sh
│
├── frontend/                      <-- 100% Open Source UI Showcase
│   ├── src/
│   │   ├── components/
│   │   │   ├── DashboardGrid.tsx
│   │   │   └── EquityChart.tsx
│   │   └── App.tsx
│   └── package.json
│
├── research/                      <-- 🔒 YOUR PRIVATE JUPYTER LAB (NEVER UPLOADED)
│   ├── notebooks/
│   │   ├── 01_data_etl.ipynb
│   │   └── 02_alpha_search.ipynb
│   └── config/
│       └── parameters_stub.json   <-- Dummy values for public repos (e.g. tp_mult=1.0)
│
└── storage/                       <-- 🔒 PRIVATE LOCAL TICK DATA (NEVER UPLOADED)
    ├── raw/
    │   └── nq_1m.csv.zst
    └── parquet/
        └── nq_minute_clean.parquet
