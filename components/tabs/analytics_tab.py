import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

def render_analytics_tab(metrics):
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("##### Trade-by-Trade PnL Waterfall (Strategy EKG Fingerprint)")
        raw_df = metrics.get("raw_trades")
        if isinstance(raw_df, pd.DataFrame) and not raw_df.empty:
            pnl_col = next((col for col in raw_df.columns if any(k in col.lower() for k in ['profit', 'net', 'pnl', 'p&l'])), None)
            if pnl_col:
                ekg_df = raw_df.copy()
                ekg_df['Clean_PnL'] = pd.to_numeric(ekg_df[pnl_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
                ekg_df['Trade_Index'] = range(len(ekg_df))
                ekg_df['Outcome'] = ekg_df['Clean_PnL'].apply(lambda x: 'Winner' if x > 0 else 'Loser')
                
                ekg_chart = alt.Chart(ekg_df).mark_bar().encode(
                    x=alt.X('Trade_Index:Q', title='Trade Sequence Index'),
                    y=alt.Y('Clean_PnL:Q', title='Trade P&L ($)'),
                    color=alt.Color('Outcome:N', scale=alt.Scale(domain=['Winner', 'Loser'], range=['#00E676', '#FF5252']), legend=None),
                    tooltip=['Trade_Index', 'Clean_PnL']
                ).properties(height=200).interactive()
                
                with st.container(border=True):
                    st.altair_chart(ekg_chart, width='stretch')
            else:
                st.info("PnL column missing for EKG chart.")
        else:
            st.warning("No trade data available.")

    with col_b:
        st.markdown("##### Returns Distribution (Dollar PnL Buckets)")
        raw_df = metrics.get("raw_trades")
        if isinstance(raw_df, pd.DataFrame) and not raw_df.empty:
            pnl_col = next((col for col in raw_df.columns if any(k in col.lower() for k in ['profit', 'net', 'pnl', 'p&l', 'return', 'gain'])), None)
            if pnl_col:
                chart_df = raw_df.copy()
                chart_df[pnl_col] = pd.to_numeric(
                    chart_df[pnl_col].astype(str).str.replace('$', '').str.replace(',', ''), 
                    errors='coerce'
                )
                chart_df = chart_df.dropna(subset=[pnl_col]).copy()
                chart_df = chart_df.rename(columns={pnl_col: 'Clean_PnL'})
                
                chart_df['Outcome'] = chart_df['Clean_PnL'].apply(
                    lambda x: 'Winner' if x > 0 else ('Loser' if x < 0 else 'Breakeven')
                )
                
                hist_chart = alt.Chart(chart_df).mark_bar().encode(
                    x=alt.X('Clean_PnL:Q', bin=alt.Bin(maxbins=29), title='Trade P&L ($)'),
                    y=alt.Y('count()', title='Number of Trades'),
                    color=alt.Color(
                        'Outcome:N', 
                        scale=alt.Scale(domain=['Winner', 'Loser', 'Breakeven'], range=['#00E676', '#FF5252', '#FFA726']), 
                        legend=None
                    ),
                    tooltip=['Clean_PnL:Q', 'count()']
                ).properties(height=200).interactive()
                
                with st.container(border=True):
                    st.altair_chart(hist_chart, width='stretch')
                    
    st.divider()
    st.markdown("##### Temporal Edge & Strategy Stability (Rolling Sharpe)")
    raw_df = metrics.get("raw_trades")
    if isinstance(raw_df, pd.DataFrame) and not raw_df.empty:
        try:
            # 🛡️ BULLETPROOF COLUMN AUTO-DETECTION
            cols_lower = {col.lower(): col for col in raw_df.columns}
            
            entry_col = next((cols_lower[c] for c in ['entry', 'start', 'open', 'time', 'date', 'fill time', 'entry time'] if c in cols_lower), None)
            exit_col = next((cols_lower[c] for c in ['exit', 'end', 'close', 'fill time', 'exit time'] if c in cols_lower), None)
            pnl_col = next((cols_lower[c] for c in ['profit', 'net', 'pnl', 'p&l', 'return'] if c in cols_lower), None)
            fee_col = next((cols_lower[c] for c in ['fee', 'commission', 'cost', 'brokerage'] if c in cols_lower), None)
            mfe_col = next((cols_lower[c] for c in ['mfe', 'maxfavorableexcursion'] if c in cols_lower), None)
            mae_col = next((cols_lower[c] for c in ['mae', 'maxadverseexcursion'] if c in cols_lower), None)
            
            if pnl_col:
                chart_df = raw_df.copy()
                chart_df['Clean_PnL'] = pd.to_numeric(chart_df[pnl_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
                
                avg_duration_str, min_dur_str, max_dur_str = "N/A", "N/A", "N/A"
                market_exposure_pct = 0.0
                total_exposure_hours = 0.0
                
                if entry_col and exit_col and entry_col != exit_col:
                    chart_df['Entry_Time'] = pd.to_datetime(chart_df[entry_col], errors='coerce')
                    chart_df['Exit_Time'] = pd.to_datetime(chart_df[exit_col], errors='coerce')
                    durations = (chart_df['Exit_Time'] - chart_df['Entry_Time']).dt.total_seconds() / 60.0
                    
                    def format_dur(mins):
                        if np.isnan(mins) or mins <= 0: return "N/A"
                        return f"{mins / 60:.1f}h" if mins >= 60 else f"{mins:.1f}m"
                        
                    avg_duration_str = format_dur(durations.mean())
                    min_dur_str = format_dur(durations.min())
                    max_dur_str = format_dur(durations.max())
                    
                    total_backtest_hours = max((chart_df['Exit_Time'].max() - chart_df['Entry_Time'].min()).total_seconds() / 3600.0, 1.0)
                    total_exposure_hours = durations.sum() / 60.0
                    market_exposure_pct = min((total_exposure_hours / total_backtest_hours) * 100, 100.0)
                
                winning_trades = chart_df[chart_df['Clean_PnL'] > 0]
                losing_trades = chart_df[chart_df['Clean_PnL'] < 0]
                
                avg_win_dur, avg_loss_dur = "N/A", "N/A"
                min_win_dur, max_win_dur = "N/A", "N/A"
                min_loss_dur, max_loss_dur = "N/A", "N/A"
                
                if entry_col and exit_col and entry_col != exit_col and not winning_trades.empty:
                    win_durs = (winning_trades['Exit_Time'] - winning_trades['Entry_Time']).dt.total_seconds() / 60.0
                    avg_win_dur = format_dur(win_durs.mean())
                    max_win_dur = format_dur(win_durs.max())
                    min_win_dur = format_dur(win_durs.min())
                    
                if entry_col and exit_col and entry_col != exit_col and not losing_trades.empty:
                    loss_durs = (losing_trades['Exit_Time'] - losing_trades['Entry_Time']).dt.total_seconds() / 60.0
                    avg_loss_dur = format_dur(loss_durs.mean())
                    max_loss_dur = format_dur(loss_durs.max())
                    min_loss_dur = format_dur(loss_durs.min())
                
                avg_win_amt = f"${winning_trades['Clean_PnL'].mean():,.2f}" if not winning_trades.empty else "$0.00"
                avg_loss_amt = f"-${abs(losing_trades['Clean_PnL'].mean()):,.2f}" if not losing_trades.empty else "$0.00"

                # 1. Streaks & Averages
                outcomes = (chart_df['Clean_PnL'] > 0).astype(int)
                streak_groups = (outcomes != outcomes.shift()).cumsum()
                win_streaks = outcomes.groupby(streak_groups).sum()
                max_win_streak = int(win_streaks.max()) if not win_streaks.empty else 0
                avg_win_streak = float(win_streaks[win_streaks > 0].mean()) if not win_streaks.empty else 0.0
                
                loss_outcomes = (chart_df['Clean_PnL'] < 0).astype(int)
                loss_streak_groups = (loss_outcomes != loss_outcomes.shift()).cumsum()
                loss_streaks = loss_outcomes.groupby(loss_streak_groups).sum()
                max_loss_streak = int(loss_streaks.max()) if not loss_streaks.empty else 0
                avg_loss_streak = float(loss_streaks[loss_streaks > 0].mean()) if not loss_streaks.empty else 0.0

                win_streak_pnl = chart_df[chart_df['Clean_PnL'] > 0]['Clean_PnL'].mean() * max_win_streak
                loss_streak_pnl = abs(chart_df[chart_df['Clean_PnL'] < 0]['Clean_PnL'].mean()) * max_loss_streak

                # 2. Tail Ratio (P95 Win / P05 Loss magnitude)
                p95_win = np.percentile(winning_trades['Clean_PnL'], 95) if not winning_trades.empty else 0.0
                p05_loss = abs(np.percentile(losing_trades['Clean_PnL'], 5)) if not losing_trades.empty else 1.0
                tail_ratio = (p95_win / p05_loss) if p05_loss > 0 else 0.0

                # 3. Holding Efficiency & MAE/MFE Efficiencies
                holding_efficiency = 0.0
                mae_efficiency = 0.0
                mfe_efficiency = 0.0
                
                if mfe_col and not chart_df.empty:
                    clean_mfe = pd.to_numeric(chart_df[mfe_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
                    valid_mfe = clean_mfe[clean_mfe > 0]
                    if not valid_mfe.empty:
                        holding_efficiency = (chart_df.loc[valid_mfe.index, 'Clean_PnL'].sum() / valid_mfe.sum()) * 100
                        mfe_efficiency = holding_efficiency
                        
                if mae_col and not chart_df.empty:
                    clean_mae = pd.to_numeric(chart_df[mae_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
                    valid_mae = clean_mae[clean_mae > 0]
                    if not valid_mae.empty:
                        mae_efficiency = max(0.0, 100.0 - (abs(chart_df.loc[valid_mae.index, 'Clean_PnL']).sum() / valid_mae.sum()) * 100)

                # 4. Kelly Criterion Optimal Leverage (%)
                total_trades = len(chart_df)
                win_rate_decimal = (len(winning_trades) / total_trades) if total_trades > 0 else 0.0
                avg_w = winning_trades['Clean_PnL'].mean() if not winning_trades.empty else 0.0
                avg_l = abs(losing_trades['Clean_PnL'].mean()) if not losing_trades.empty else 1.0
                payoff_r = (avg_w / avg_l) if avg_l > 0 else 1.0
                kelly_pct = max(0.0, (win_rate_decimal - ((1.0 - win_rate_decimal) / payoff_r)) * 100) if payoff_r > 0 else 0.0

                # 5. Commission Drag & Alpha Velocity
                gross_profit = winning_trades['Clean_PnL'].sum() if not winning_trades.empty else 0.0
                total_fees = abs(pd.to_numeric(chart_df[fee_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce').sum()) if fee_col and not chart_df.empty else float(len(chart_df) * 1.24)
                fee_drag_pct = (total_fees / gross_profit) * 100 if gross_profit > 0 else 0.0
                
                net_total_pnl = chart_df['Clean_PnL'].sum()
                alpha_velocity = (net_total_pnl / total_exposure_hours) if total_exposure_hours > 0 else 0.0

                # 📊 3-COLUMN PROFESSIONAL INSTITUTIONAL DIAGNOSTICS CARD (No Emojis, Balanced Height)
                html_card = f"""<div style="background-color: #121C24; border: 1px solid #475569; border-left: 4px solid #00E676; padding: 18px 22px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); margin-bottom: 20px; color: #F8FAFC; font-size: 13px;"><div style="font-weight: 600; color: #94A3B8; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-size: 14px;">EXECUTION, LIQUIDITY & ADVANCED TAIL DIAGNOSTICS</div><div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 14px;"><div><b>Durations (Avg/Min/Max):</b><br>Overall: {avg_duration_str} / {min_dur_str} / {max_dur_str}<br><span style="color: #00E676;">Win: {avg_win_dur} ({avg_win_amt})</span><br><span style="color: #FF5252;">Loss: {avg_loss_dur} ({avg_loss_amt})</span><br><b>Exposure:</b> {market_exposure_pct:.1f}% ({total_exposure_hours:.1f}h)</div><div><b>Max Streaks (Max / Avg):</b><br><span style="color: #00E676;">{max_win_streak} Wins (Avg {avg_win_streak:.1f}) | +${win_streak_pnl:,.0f}</span><br><span style="color: #FF5252;">{max_loss_streak} Losses (Avg {avg_loss_streak:.1f}) | -${loss_streak_pnl:,.0f}</span><br><b>Alpha Velocity:</b> ${alpha_velocity:,.2f}/hr<br><b>Kelly Optimal Lev:</b> {kelly_pct:.1f}%</div><div><b>Tail Ratio (P95/P05):</b> {tail_ratio:.2f}x<br><b>Holding Efficiency:</b> {holding_efficiency:.1f}% of MFE<br><b>MAE / MFE Eff:</b> {mae_efficiency:.1f}% / {mfe_efficiency:.1f}%<br><b>Payoff Asymmetry:</b> {payoff_r:.2f}x<br><b>Commission Drag:</b> {fee_drag_pct:.2f}% (${total_fees:,.2f})</div></div></div>"""
                
                st.markdown(html_card, unsafe_allow_html=True)

                window_size = min(30, max(2, len(chart_df) // 2))
                chart_df['Rolling_Sharpe'] = (
                    chart_df['Clean_PnL'].rolling(window=window_size).mean() / 
                    (chart_df['Clean_PnL'].rolling(window=window_size).std() + 1e-9)
                ) * np.sqrt(252)
                
                rolling_df = chart_df.dropna(subset=['Rolling_Sharpe']).reset_index(drop=True)
                
                if not rolling_df.empty:
                    rolling_df['Trade_Index'] = rolling_df.index
                    
                    line_chart = alt.Chart(rolling_df).mark_line(color='#FFA726', strokeWidth=2).encode(
                        x=alt.X('Trade_Index:Q', title='Trade Sequence Index'),
                        y=alt.Y('Rolling_Sharpe:Q', title='Rolling Sharpe Ratio'),
                        tooltip=['Trade_Index', 'Rolling_Sharpe']
                    ).properties(height=240).interactive()
                    
                    with st.container(border=True):
                        st.markdown("**Strategy Stability (Rolling Sharpe Ratio)**")
                        st.altair_chart(line_chart, width='stretch')
                else:
                    st.info("Not enough trades in this backtest to calculate rolling stability.")
            else:
                st.warning("PnL column not found in trades CSV for temporal analytics.")
        except Exception as ex:
            st.warning(f"Error rendering temporal diagnostics: {ex}")
    else:
        st.info("No raw trades available for temporal analytics.")