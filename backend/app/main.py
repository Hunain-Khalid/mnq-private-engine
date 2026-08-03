from fastapi import FastAPI, HTTPException
from app.database import query_15m_bars
import pandas as pd

# Open Source Router Boilerplate
app = FastAPI(title="Alpha Flush Execution Hub")

try:
    # 🔒 DYNAMIC IMPORT TRICK:
        # Try to load your secret sauce. If it's running locally on your PC, it works.
        # If a recruiter builds it from GitHub, it safely falls back to a dummy class!
    from app.secret_sauce.alpha_signals import calculate_proprietary_signals
except ImportError:
    # Open Source Dummy Fallback so the code doesn't crash on public repos
    # Public placeholder mock function (Secret Sauce stays hidden)
    df['entries'] = df['close'] > df['open']
    df['tp_target'] = df['close'] * 1.01
    df['sl_target'] = df['close'] * 0.99
    return df

@app.get("/api/v1/backtest")
def run_strategy_backtest(tp_mult: float = 3.57, sl_mult: float = 2.49):
    try:
        # 1. Fetch data from your open-source database wrapper
        df = query_15m_bars()

        # 2. Run the signal module (calculates using hidden math if local)
        df_with_signals = calculate_proprietary_signals(df)

        # 3. Process VectorBT metrics package safely...
        # (The engine uses df_with_signals['entries'] to generate JSON for React)
        return {"status": "success", "total_trades": len(df_with_signals[df_with_signals['entries'] == True])}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
