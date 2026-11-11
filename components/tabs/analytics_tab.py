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
    
    # ==========================================
    # ⚖️ LONG VS SHORT STRUCTURAL PERFORMANCE SPLIT
    # ==========================================
    raw_df = metrics.get("raw_trades")
    eq_df = metrics.get("equity_curve")

    #st.markdown("##### Temporal Edge & Strategy Stability (Rolling Sharpe)")
    
    if isinstance(raw_df, pd.DataFrame) and not raw_df.empty:
        try:
            cols_lower = {col.lower(): col for col in raw_df.columns}
            type_col = next((cols_lower[c] for c in ['type', 'direction', 'side', 'action'] if c in cols_lower), None)
            pnl_col = next((cols_lower[c] for c in ['profit', 'net', 'pnl', 'p&l', 'return'] if c in cols_lower), None)
            
            if type_col and pnl_col:
                temp_df = raw_df.copy()
                temp_df['Clean_Direction'] = temp_df[type_col].astype(str).str.lower()
                temp_df['Clean_PnL'] = pd.to_numeric(temp_df[pnl_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
                
                longs = temp_df[temp_df['Clean_Direction'].str.contains('buy|long', na=False)]
                shorts = temp_df[temp_df['Clean_Direction'].str.contains('sell|short', na=False)]
                
                def get_split_stats(df):
                    if df.empty: return 0, 0.0, "0.0%", "$0.00"
                    cnt = len(df)
                    pnl = df['Clean_PnL'].sum()
                    wr = f"{(len(df[df['Clean_PnL'] > 0]) / cnt) * 100:.1f}%"
                    avg_pnl = f"${df['Clean_PnL'].mean():,.2f}"
                    return cnt, pnl, wr, avg_pnl
                
                l_cnt, l_pnl, l_wr, l_avg = get_split_stats(longs)
                s_cnt, s_pnl, s_wr, s_avg = get_split_stats(shorts)
                
                col_l, col_s = st.columns(2)
                with col_l:
                    st.markdown(f"""
                        <div style="background-color: #121C24; border: 1px solid #334155; border-left: 4px solid #00E676; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px; font-size: 13px;">
                            <div style="color: #00E676; font-weight: 600; margin-bottom: 4px;">LONG COHORT ({l_cnt} Trades)</div>
                            <div><b>Net P&L:</b> ${l_pnl:,.2f} | <b>Win Rate:</b> {l_wr} | <b>Avg:</b> {l_avg}</div>
                        </div>
                    """, unsafe_allow_html=True)
                with col_s:
                    st.markdown(f"""
                        <div style="background-color: #121C24; border: 1px solid #334155; border-left: 4px solid #FF5252; padding: 10px 14px; border-radius: 6px; margin-bottom: 12px; font-size: 13px;">
                            <div style="color: #FF5252; font-weight: 600; margin-bottom: 4px;">SHORT COHORT ({s_cnt} Trades)</div>
                            <div><b>Net P&L:</b> ${s_pnl:,.2f} | <b>Win Rate:</b> {s_wr} | <b>Avg:</b> {s_avg}</div>
                        </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            pass

    
    
    ulcer_index_val = 0.0
    if isinstance(eq_df, pd.DataFrame) and not eq_df.empty and 'Equity' in eq_df.columns:
        eq_series = eq_df['Equity']
        cum_max = eq_series.cummax()
        drawdowns_pct = (eq_series - cum_max) / cum_max
        ulcer_index_val = np.sqrt(np.mean(drawdowns_pct ** 2)) * 100

    if isinstance(raw_df, pd.DataFrame) and not raw_df.empty:
        try:
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
                
                avg_duration_str = "N/A"
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
                    
                    total_backtest_hours = max((chart_df['Exit_Time'].max() - chart_df['Entry_Time'].min()).total_seconds() / 3600.0, 1.0)
                    total_exposure_hours = durations.sum() / 60.0
                    market_exposure_pct = min((total_exposure_hours / total_backtest_hours) * 100, 100.0)
                
                winning_trades = chart_df[chart_df['Clean_PnL'] > 0]
                losing_trades = chart_df[chart_df['Clean_PnL'] < 0]
                
                avg_win_dur, avg_loss_dur = "N/A", "N/A"
                if entry_col and exit_col and entry_col != exit_col and not winning_trades.empty:
                    win_durs = (winning_trades['Exit_Time'] - winning_trades['Entry_Time']).dt.total_seconds() / 60.0
                    avg_win_dur = format_dur(win_durs.mean())
                if entry_col and exit_col and entry_col != exit_col and not losing_trades.empty:
                    loss_durs = (losing_trades['Exit_Time'] - losing_trades['Entry_Time']).dt.total_seconds() / 60.0
                    avg_loss_dur = format_dur(loss_durs.mean())
                
                avg_win_amt = f"${winning_trades['Clean_PnL'].mean():,.2f}" if not winning_trades.empty else "$0.00"
                avg_loss_amt = f"-${abs(losing_trades['Clean_PnL'].mean()):,.2f}" if not losing_trades.empty else "$0.00"

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

                p95_win = np.percentile(winning_trades['Clean_PnL'], 95) if not winning_trades.empty else 0.0
                p05_loss = abs(np.percentile(losing_trades['Clean_PnL'], 5)) if not losing_trades.empty else 1.0
                tail_ratio = (p95_win / p05_loss) if p05_loss > 0 else 0.0

                avg_mae_val = abs(pd.to_numeric(chart_df[mae_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce').mean()) if mae_col and not chart_df.empty else 0.0
                avg_mfe_val = pd.to_numeric(chart_df[mfe_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce').mean() if mfe_col and not chart_df.empty else 0.0
                
                clean_mfe = pd.to_numeric(chart_df[mfe_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce') if mfe_col and not chart_df.empty else pd.Series([1.0])
                total_realized_pnl = chart_df['Clean_PnL'].sum()
                total_possible_mfe = clean_mfe.sum() if not clean_mfe.empty else 1.0
                profit_capture_rate = (total_realized_pnl / total_possible_mfe) * 100 if total_possible_mfe > 0 else 0.0

                median_win_dur = win_durs.median() if 'win_durs' in locals() and not win_durs.empty else 25.0
                overstay_drag = 0.0
                if entry_col and exit_col and not chart_df.empty:
                    temp_overstay = chart_df.copy()
                    temp_overstay['Dur_Mins'] = (temp_overstay['Exit_Time'] - temp_overstay['Entry_Time']).dt.total_seconds() / 60.0
                    overstay_drag = temp_overstay[(temp_overstay['Dur_Mins'] > (median_win_dur * 2)) & (temp_overstay['Clean_PnL'] < 0)]['Clean_PnL'].sum()

                total_trades = len(chart_df)
                win_rate_decimal = (len(winning_trades) / total_trades) if total_trades > 0 else 0.0
                avg_w = winning_trades['Clean_PnL'].mean() if not winning_trades.empty else 0.0
                avg_l = abs(losing_trades['Clean_PnL'].mean()) if not losing_trades.empty else 1.0
                payoff_r = (avg_w / avg_l) if avg_l > 0 else 1.0
                kelly_pct = max(0.0, (win_rate_decimal - ((1.0 - win_rate_decimal) / payoff_r)) * 100) if payoff_r > 0 else 0.0

                gross_profit = winning_trades['Clean_PnL'].sum() if not winning_trades.empty else 0.0
                total_fees = abs(pd.to_numeric(chart_df[fee_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce').sum()) if fee_col and not chart_df.empty else float(len(chart_df) * 1.24)
                fee_drag_pct = (total_fees / gross_profit) * 100 if gross_profit > 0 else 0.0
                
                net_total_pnl = chart_df['Clean_PnL'].sum()
                alpha_velocity = (net_total_pnl / total_exposure_hours) if total_exposure_hours > 0 else 0.0
                trades_per_day = total_trades / max((total_exposure_hours / 6.5), 1.0)

                # 📊 4-COLUMN ULTRA-HIGH-DENSITY INSTITUTIONAL DIAGNOSTICS CARD
                html_card = f"""<div style="background-color: #121C24; border: 1px solid #475569; border-left: 4px solid #00E676; padding: 16px 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.4); margin-bottom: 20px; color: #F8FAFC; font-size: 12px;">
                    <div style="font-weight: 600; color: #94A3B8; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.5px; font-size: 13px;">EXECUTION, LIQUIDITY & ADVANCED TAIL DIAGNOSTICS</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 12px;">
                        <div>
                            <b>Durations:</b> Overall: {avg_duration_str}<br>
                            <span style="color: #00E676;">Win: {avg_win_dur} ({avg_win_amt})</span><br>
                            <span style="color: #FF5252;">Loss: {avg_loss_dur} ({avg_loss_amt})</span><br>
                            <b>Exposure:</b> {market_exposure_pct:.1f}% ({total_exposure_hours:.1f}h)
                        </div>
                        <div>
                            <b>Streaks (Max / Avg):</b><br>
                            <span style="color: #00E676;">{max_win_streak} Wins ({avg_win_streak:.1f}) | +${win_streak_pnl:,.0f}</span><br>
                            <span style="color: #FF5252;">{max_loss_streak} Losses ({avg_loss_streak:.1f}) | -${loss_streak_pnl:,.0f}</span><br>
                            <b>Alpha Velocity:</b> ${alpha_velocity:,.2f}/hr
                        </div>
                        <div>
                            <b>Tail Ratio:</b> {tail_ratio:.2f}x | <b>UI:</b> {ulcer_index_val:.1f}%<br>
                            <b>Profit Capture:</b> {profit_capture_rate:.1f}% of MFE<br>
                            <b>Avg MFE / MAE:</b> ${avg_mfe_val:,.0f} / -${avg_mae_val:,.0f}<br>
                            <b>Overstay Drag:</b> ${abs(overstay_drag):,.0f}
                        </div>
                        <div>
                            <b>Payoff Asym:</b> {payoff_r:.2f}x<br>
                            <b>Kelly Lev:</b> {kelly_pct:.1f}%<br>
                            <b>Commission Drag:</b> {fee_drag_pct:.2f}% (${total_fees:,.2f})<br>
                            <b>Execution Density:</b> {trades_per_day:.1f} trd/day
                        </div>
                    </div>
                </div>"""
                
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
                    ).properties(height=220).interactive()
                    
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