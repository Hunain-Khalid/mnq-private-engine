import streamlit as st
import pandas as pd
import numpy as np
from components.charts import render_interactive_equity_chart
from components.metric_cards import institutional_metric

def render_equity_tab(metrics):
    eq_df = metrics.get("equity_curve")
    if isinstance(eq_df, pd.DataFrame) and not eq_df.empty:
        render_interactive_equity_chart(eq_df)
        
        # 🏛️ 4x5 INSTITUTIONAL QUANT GRID CALCULATIONS
        eq_series = eq_df['Equity']
        start_val = eq_series.iloc[0]
        end_val = eq_series.iloc[-1]
        peak_val = eq_series.max()
        trough_val = eq_series.min()
        net_pnl = end_val - start_val
        trades_count = metrics.get('total_trades', 0)
        
        try:
            start_date = eq_df.index[0]
            end_date = eq_df.index[-1]
            days_spanned = (end_date - start_date).days
            years_spanned = max(days_spanned / 365.25, 0.1)
        except Exception:
            years_spanned = 1.0

        win_cnt = metrics.get('winners', 0)
        loss_cnt = metrics.get('losers', 0)
        
        raw_trades_df = metrics.get("raw_trades")
        avg_win_val = 0.0
        avg_loss_val = 0.0
        total_fees_val = 0.0
        
        if isinstance(raw_trades_df, pd.DataFrame) and not raw_trades_df.empty:
            pnl_col = next((col for col in raw_trades_df.columns if any(k in col.lower() for k in ['profit', 'net', 'pnl', 'p&l', 'return', 'gain'])), None)
            fee_col = next((col for col in raw_trades_df.columns if any(k in col.lower() for k in ['fee', 'commission'])), None)
            
            if pnl_col:
                clean_pnl = pd.to_numeric(raw_trades_df[pnl_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
                avg_win_val = clean_pnl[clean_pnl > 0].mean() if win_cnt > 0 else 0.0
                avg_loss_val = abs(clean_pnl[clean_pnl < 0].mean()) if loss_cnt > 0 else 0.0
                
            if fee_col:
                clean_fees = pd.to_numeric(raw_trades_df[fee_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
                total_fees_val = clean_fees.sum()

        max_dd_val = peak_val - trough_val
        recovery_factor = abs(net_pnl / max_dd_val) if max_dd_val > 0 else 0.0
        expectancy_val = net_pnl / trades_count if trades_count > 0 else 0.0
        payoff_ratio = (avg_win_val / avg_loss_val) if avg_loss_val > 0 else 0.0
        
        cagr_approx = ((end_val / start_val) ** (1 / years_spanned)) - 1 if start_val > 0 else 0.0
        max_dd_decimal = max_dd_val / peak_val if peak_val > 0 else 0.001
        calmar_val = (cagr_approx / max_dd_decimal) if max_dd_decimal > 0 else 0.0

        returns = eq_series.pct_change().dropna()
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0.001
        mean_return = returns.mean() * 252
        sortino_val = (mean_return / downside_std) if downside_std > 0 else 0.0

        if isinstance(raw_trades_df, pd.DataFrame) and not raw_trades_df.empty and pnl_col:
            pnl_series = pd.to_numeric(raw_trades_df[pnl_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce').dropna()
            sqn_val = (pnl_series.mean() / pnl_series.std()) * np.sqrt(len(pnl_series)) if len(pnl_series) > 1 and pnl_series.std() > 0 else 0.0
        else:
            sqn_val = 0.0

        cum_max = eq_series.cummax()
        drawdowns_pct = (eq_series - cum_max) / cum_max
        ulcer_index = np.sqrt(np.mean(drawdowns_pct ** 2)) * 100

        mae_col = next((col for col in raw_trades_df.columns if 'mae' in col.lower()), None) if isinstance(raw_trades_df, pd.DataFrame) else None
        mfe_col = next((col for col in raw_trades_df.columns if 'mfe' in col.lower()), None) if isinstance(raw_trades_df, pd.DataFrame) else None
        avg_mae = f"${raw_trades_df[mae_col].mean():,.2f}" if mae_col and not raw_trades_df.empty else "N/A"
        avg_mfe = f"${raw_trades_df[mfe_col].mean():,.2f}" if mfe_col and not raw_trades_df.empty else "N/A"

        # 🏛️ RENDER 4x5 QUANT GRID
        r1_c1, r1_c2, r1_c3, r1_c4, r1_c5 = st.columns(5)
        
        def safe_float(val, default=0.0):
            try:
                return float(str(val).replace('x', '').replace('%', '').strip())
            except (ValueError, TypeError):
                return default

        sharpe_raw = metrics.get("sharpe", "N/A")
        sharpe_float = safe_float(sharpe_raw, 0.0)
        pf_raw = metrics.get("profit_factor", "N/A")
        pf_float = safe_float(pf_raw, 1.0)
        raw_max_dd_str = metrics.get("max_drawdown", "31.7%")

        institutional_metric(r1_c1, "Sharpe Ratio", sharpe_raw, is_positive=sharpe_float >= 0)
        institutional_metric(r1_c2, "Sortino Ratio", f"{sortino_val:.2f}", is_positive=sortino_val >= 0)
        institutional_metric(r1_c3, "Calmar Ratio", f"{calmar_val:.2f}", is_positive=calmar_val >= 0)
        institutional_metric(r1_c4, "Profit Factor", pf_raw, is_positive=pf_float >= 1.0)
        institutional_metric(r1_c5, "System Quality (SQN)", f"{sqn_val:.2f}", is_positive=sqn_val >= 0)

        r2_c1, r2_c2, r2_c3, r2_c4, r2_c5 = st.columns(5)
        institutional_metric(r2_c1, "Total Trades", trades_count, is_positive=True)
        institutional_metric(r2_c2, "Win Rate", metrics.get("win_rate", "0.0%"), is_positive=True)
        institutional_metric(r2_c3, "Expectancy ($)", f"${expectancy_val:,.2f}", is_positive=expectancy_val >= 0)
        institutional_metric(r2_c4, "Payoff Ratio", f"{payoff_ratio:.2f}x", is_positive=payoff_ratio >= 1.0)
        institutional_metric(r2_c5, "Ulcer Index", f"{ulcer_index:.2f}%", is_positive=ulcer_index < 10.0)

        r3_c1, r3_c2, r3_c3, r3_c4, r3_c5 = st.columns(5)
        institutional_metric(r3_c1, "Avg Win", f"${avg_win_val:,.2f}" if win_cnt > 0 else "$0.00", is_positive=True)
        institutional_metric(r3_c2, "Avg Loss", f"-${avg_loss_val:,.2f}" if loss_cnt > 0 else "$0.00", is_positive=False)
        institutional_metric(r3_c3, "Avg MAE", avg_mae, is_positive=False)
        institutional_metric(r3_c4, "Avg MFE", avg_mfe, is_positive=True)
        institutional_metric(r3_c5, "Recovery Factor", f"{recovery_factor:.2f}x", is_positive=recovery_factor >= 1.0)

        r4_c1, r4_c2, r4_c3, r4_c4, r4_c5 = st.columns(5)
        institutional_metric(r4_c1, "Net P&L", f"${net_pnl:,.0f}", delta=f"{(net_pnl/start_val)*100:.1f}%", is_positive=net_pnl >= 0)
        institutional_metric(r4_c2, "Total Fees Paid", f"${total_fees_val:,.2f}", is_positive=False)
        institutional_metric(r4_c3, "Max Drawdown", f"{raw_max_dd_str} (-${max_dd_val:,.0f})", is_positive=False)
        institutional_metric(r4_c4, "Winners / Losers", f"{win_cnt}W / {loss_cnt}L", is_positive=win_cnt >= loss_cnt)
        institutional_metric(r4_c5, "Breakeven Trades", metrics.get("breakevens", 0), is_positive=True)