import duckdb
import vectorbt as vbt
import pandas as pd
import numpy as np

print("🦆 [Research] Connecting to DuckDB storage tier...")
con = duckdb.connect("./storage/alpha_node.duckdb", read_only=True)

print("📊 [Research] Querying NQ RTH minute bars into memory...")
df = con.execute("""
SELECT CAST(datetime AS TIMESTAMP) as dt, close, log_return
FROM nq_1m
ORDER BY datetime ASC;
""").fetchdf()
con.close()

df.set_index('dt', inplace=True)

# --- SAFE SYNTHETIC PRICE BUILDER ---
# Instead of unbounded cumprod() on log returns which causes floating-point overflow,
# we use simple percentage returns or clip extreme returns to prevent overflow.
df['safe_return'] = df['log_return'].clip(lower=-0.05, upper=0.05) # Cap single-minute moves at +/- 5%
synthetic_close = 10000 * (1 + df['safe_return']).cumprod()

# Sanitize: Drop NaNs, Infs, and non-positive values
synthetic_close = synthetic_close.replace([np.inf, -np.inf], np.nan).dropna()
synthetic_close = synthetic_close[synthetic_close > 0]

print(f"📈 [Research] Loaded {len(synthetic_close):,} clean synthetic price bars into VectorBT!")

# ==========================================
# VECTORIZED STRATEGY SIMULATION (VectorBT)
# ==========================================
print("⚡ [Research] Running VectorBT vectorized simulation on clean synthetic close...")

fast_window = 10
slow_window = 50

fast_ma = vbt.MA.run(synthetic_close, window=fast_window)
slow_ma = vbt.MA.run(synthetic_close, window=slow_window)

entries = fast_ma.ma_crossed_above(slow_ma.ma)
exits = fast_ma.ma_crossed_below(slow_ma.ma)

portfolio = vbt.Portfolio.from_signals(
    close=synthetic_close,
    entries=entries,
    exits=exits,
    init_cash=100000.0,
    fees=0.0002,
    freq='1min'
)

print("\n" + "="*40)
print(" 🏛️ VECTORBT PERFORMANCE TEAR SHEET (OVERFLOW-PROOF)")
print("="*40)
stats = portfolio.stats()
print(stats)
print("="*40)

# Save the interactive chart as an HTML file
fig = portfolio.plot()
fig.write_html("backtest_deck.html")
print("📊 [Research] Interactive deck saved as 'backtest_deck.html'! Open it in your browser.")