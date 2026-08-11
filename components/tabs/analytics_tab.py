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
            entry_col = next((col for col in raw_df.columns if any(k in col.lower() for k in ['entry', 'start', 'open', 'time'])), None)
            exit_col = next((col for col in raw_df.columns if any(k in col.lower() for k in ['exit', 'end', 'close'])), None)
            pnl_col = next((col for col in raw_df.columns if any(k in col.lower() for k in ['profit', 'net', 'pnl', 'p&l'])), None)
            
            if entry_col and pnl_col:
                chart_df = raw_df.copy()
                chart_df['Entry_Time'] = pd.to_datetime(chart_df[entry_col], errors='coerce')
                chart_df['Clean_PnL'] = pd.to_numeric(chart_df[pnl_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
                
                avg_duration_str, min_dur_str, max_dur_str = "N/A", "N/A", "N/A"
                if exit_col:
                    chart_df['Exit_Time'] = pd.to_datetime(chart_df[exit_col], errors='coerce')
                    durations = (chart_df['Exit_Time'] - chart_df['Entry_Time']).dt.total_seconds() / 60.0
                    def format_dur(mins):
                        if np.isnan(mins): return "N/A"
                        return f"{mins / 60:.1f}h" if mins >= 60 else f"{mins:.1f}m"
                    avg_duration_str = format_dur(durations.mean())
                    min_dur_str = format_dur(durations.min())
                    max_dur_str = format_dur(durations.max())
                
                winning_trades = chart_df[chart_df['Clean_PnL'] > 0]
                losing_trades = chart_df[chart_df['Clean_PnL'] < 0]
                
                win_durs = (winning_trades['Exit_Time'] - winning_trades['Entry_Time']).dt.total_seconds() / 60.0 if not winning_trades.empty and exit_col else pd.Series([0])
                loss_durs = (losing_trades['Exit_Time'] - losing_trades['Entry_Time']).dt.total_seconds() / 60.0 if not losing_trades.empty and exit_col else pd.Series([0])
                
                avg_win_dur = format_dur(win_durs.mean())
                max_win_dur = format_dur(win_durs.max())
                min_win_dur = format_dur(win_durs.min())
                
                avg_loss_dur = format_dur(loss_durs.mean())
                max_loss_dur = format_dur(loss_durs.max())
                min_loss_dur = format_dur(loss_durs.min())
                
                avg_win_amt = f"${winning_trades['Clean_PnL'].mean():,.2f}" if not winning_trades.empty else "$0.00"
                avg_loss_amt = f"-${abs(losing_trades['Clean_PnL'].mean()):,.2f}" if not losing_trades.empty else "$0.00"

                st.markdown(f"""
                    <div style="
                        background-color: #121C24;
                        border: 1px solid #475569;
                        border-left: 4px solid #00E676;
                        padding: 16px 20px;
                        border-radius: 8px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                        margin-bottom: 20px;
                        color: #F8FAFC;
                        font-size: 14px;
                    ">
                        <div style="font-weight: 600; color: #94A3B8; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">📊 Execution & Duration Diagnostics</div>
                        <span style="margin-right: 20px;">⏱️ <b>Duration (Avg/Min/Max):</b> {avg_duration_str} / {min_dur_str} / {max_dur_str}</span><br>
                        <span style="margin-right: 20px; color: #00E676;">🟢 <b>Win Dur (Avg/Min/Max):</b> {avg_win_dur} / {min_win_dur} / {max_win_dur} ({avg_win_amt})</span><br>
                        <span style="color: #FF5252;">🔴 <b>Loss Dur (Avg/Min/Max):</b> {avg_loss_dur} / {min_loss_dur} / {max_loss_dur} ({avg_loss_amt})</span>
                    </div>
                """, unsafe_allow_html=True)

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
        except Exception as e:
            pass
    else:
        st.info("Required timestamp and PnL columns not found for temporal analytics.")