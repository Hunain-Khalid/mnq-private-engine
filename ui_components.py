import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from backend_metrics import cached_read_markdown, cached_read_file_bytes, run_monte_carlo_simulation
from ui_styles import inject_global_institutional_theme
from pathlib import Path

def render_sidebar():
    """Renders the standard system sidebar configuration and returns selected page."""
    inject_global_institutional_theme()
    st.sidebar.title("Alpha Flush Node")
    page = st.sidebar.radio(
        "Navigation", 
        ["Backtests (IS / OOS)", "Live / Paper Trading", "Engineering Archive"], 
        key="nav_radio"
    )
    st.sidebar.divider()
    st.sidebar.header("Pipeline Architecture")
    st.sidebar.markdown("""
    1. **Model:** QuantConnect Cloud (Python/LEAN)
    2. **Obfuscation:** Git-ignored `params.json` & `MAPPINGS.txt`
    3. **Artifacts:** Compressed PDFs + Minified JSON + CSV Logs
    4. **Hosting:** Streamlit Community Cloud
    """)
    return page

def institutional_metric(col, label, value, delta=None, is_positive=True):
    """Renders a metric card with explicit green or red institutional styling based on value sign."""
    border_color = "#00E676" if is_positive else "#FF5252"
    bg_color = "#121C24" if is_positive else "#2A1215"
    text_color = "#FFFFFF" if is_positive else "#FF5252"
    
    col.markdown(f"""
        <div style="
            background-color: {bg_color};
            border: 1px solid #334155;
            border-left: 4px solid {border_color};
            padding: 14px 18px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            margin-bottom: 10px;
        ">
            <div style="font-size: 12px; color: #94A3B8; margin-bottom: 4px;">{label}</div>
            <div style="font-size: 20px; font-weight: 600; color: {text_color};">{value}</div>
            {f'<div style="font-size: 12px; margin-top: 4px; color: {border_color};">{delta}</div>' if delta else ''}
        </div>
    """, unsafe_allow_html=True)

@st.fragment
def render_monte_carlo_fragment(metrics, base_name):
    """Isolated Monte Carlo fragment with spaghetti paths, P5-P95 bands, and drawdown histogram."""
    st.markdown("### Advanced Monte Carlo Stress Test & Tail Risk")
    st.markdown("Bootstrap simulation with P5/P95 tail bounds, individual path variance (spaghetti plots), and max drawdown distribution frequency.")
    
    raw_df = metrics.get("raw_trades")
    if isinstance(raw_df, pd.DataFrame) and not raw_df.empty:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            num_sims = st.slider("Number of Simulations", 100, 10000, 1000, step=100, key=f"sims_{base_name}")
        with col_s2:
            horizon = st.slider("Forward Trade Horizon", 50, 500, 100, step=50, key=f"horiz_{base_name}")
        
        mc_df, ruin_prob, spaghetti_df, max_drawdowns = run_monte_carlo_simulation(raw_df, num_simulations=num_sims, num_trades_to_project=horizon)
        
        if mc_df is not None:
            col_m1, col_m2 = st.columns(2)
            
            ruin_safe = ruin_prob < 5.0
            institutional_metric(
                col_m1, 
                "Estimated Risk of Ruin (>20% DD)", 
                f"{ruin_prob:.2f}%", 
                delta="Prop Firm Safe" if ruin_safe else "High Risk", 
                is_positive=ruin_safe
            )
            
            median_pnl_val = mc_df['Median'].iloc[-1] - 1000000.0
            institutional_metric(
                col_m2, 
                "Projected Median Ending PnL", 
                f"${median_pnl_val:,.0f}", 
                is_positive=(median_pnl_val >= 0)
            )
            
            spaghetti_layer = alt.Chart(spaghetti_df).mark_line(color='#475569', strokeWidth=1.0, opacity=0.65).encode(
                x='Trade_Index:Q',
                y='Equity:Q',
                detail='Simulation:N'
            )
            
            melted_mc = mc_df.melt('Trade_Index', var_name='Percentile', value_name='Equity')
            bands_layer = alt.Chart(melted_mc).mark_line(strokeWidth=2.2, opacity=0.85).encode(
                x=alt.X('Trade_Index:Q', title='Simulated Trade Index'),
                y=alt.Y('Equity:Q', scale=alt.Scale(zero=False), title='Projected Equity ($)'),
                color=alt.Color('Percentile:N', scale=alt.Scale(
                    domain=['P5', 'P10', 'Median', 'P90', 'P95'], 
                    range=['#FF1744', '#FF5252', '#FFA726', '#00E676', '#00C853']
                ))
            )
            
            combined_chart = (spaghetti_layer + bands_layer).properties(height=320).interactive()
            
            st.markdown("##### Monte Carlo Equity Paths (Spaghetti Variance + P5-P95 Tail Bounds)")
            with st.container(border=True):
                st.altair_chart(combined_chart, width='stretch')
                
            st.markdown("##### Maximum Drawdown Distribution Across Simulations")
            dd_df = pd.DataFrame({"Max_Drawdown_Pct": max_drawdowns})
            
            dd_hist = alt.Chart(dd_df).mark_bar(color='#FF5252', opacity=0.8).encode(
                x=alt.X('Max_Drawdown_Pct:Q', bin=alt.Bin(maxbins=30), title='Max Drawdown (%)'),
                y=alt.Y('count()', title='Frequency of Simulations'),
                tooltip=['count()']
            ).properties(height=200).interactive()
            
            with st.container(border=True):
                st.altair_chart(dd_hist, width='stretch')
        else:
            st.warning("Insufficient trade data to run Monte Carlo simulation.")
    else:
        st.info("No raw trades available for this model to generate Monte Carlo simulations.")

@st.fragment
def render_interactive_equity_chart(metrics, eq_df):
    """Renders the clean single-color institutional equity curve, starting equity baseline, and 12-metric grid."""
    # 🛡️ Safely extract date range for display (handles datetime vs integer indexes)
    try:
        min_idx = eq_df.index.min()
        max_idx = eq_df.index.max()
        start_date_str = min_idx.strftime('%Y-%m-%d') if hasattr(min_idx, 'strftime') else str(min_idx)
        end_date_str = max_idx.strftime('%Y-%m-%d') if hasattr(max_idx, 'strftime') else str(max_idx)
    except Exception:
        start_date_str = "N/A"
        end_date_str = "N/A"
    
    st.markdown(f"**Backtest Date Range:** `{start_date_str}` ➔ `{end_date_str}`")
    st.markdown(f"**Backtest Date Range:** `{start_date_str}` ➔ `{end_date_str}`")

    start_cap_val = eq_df['Equity'].iloc[0]
    
    line = alt.Chart(eq_df.reset_index()).mark_line(
        color='#00E676', strokeWidth=2.2
    ).encode(
        x=alt.X('Time:T', title='Timeline (Trade Exit Date)'),
        y=alt.Y('Equity:Q', scale=alt.Scale(zero=False), title='Account Equity ($)'),
        tooltip=['Time:T', 'Equity:Q']
    )
    
    baseline_rule = alt.Chart(pd.DataFrame({'y': [start_cap_val]})).mark_rule(
        color='#FFA726', strokeDash=[4, 4], strokeWidth=1.5
    ).encode(y='y:Q')
    
    chart = (line + baseline_rule).properties(height=220).interactive()
    st.caption("Dashed Line: Starting Equity Baseline ($1,000,000)")
    
    with st.container(border=True):
        st.altair_chart(chart, width='stretch')

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

    avg_win_pct = (avg_win_val / start_val) * 100 if start_val > 0 else 0.0
    avg_loss_pct = (avg_loss_val / start_val) * 100 if start_val > 0 else 0.0
    raw_max_dd_str = metrics.get("max_drawdown", "31.7%")

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

    # ==========================================
    # 🏛️ 4x5 INSTITUTIONAL QUANT GRID (20 METRICS)
    # ==========================================
    r1_c1, r1_c2, r1_c3, r1_c4, r1_c5 = st.columns(5)
    
    # 🛡️ Bulletproof Sharpe conversion
    sharpe_raw = metrics.get("sharpe", "N/A")
    try:
        sharpe_float = float(sharpe_raw)
    except (ValueError, TypeError):
        sharpe_float = 0.0

    institutional_metric(r1_c1, "Sharpe Ratio", sharpe_raw, is_positive=sharpe_float >= 0)
    institutional_metric(r1_c2, "Sortino Ratio", f"{sortino_val:.2f}", is_positive=sortino_val >= 0)
    institutional_metric(r1_c3, "Calmar Ratio", f"{calmar_val:.2f}", is_positive=calmar_val >= 0)
    institutional_metric(r1_c4, "Profit Factor", metrics.get("profit_factor", "N/A"), is_positive=float(metrics.get("profit_factor", 1) or 1) >= 1.0)
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

def render_pro_tabs(metrics, md_path, pdf_path, base_name, matching_trades, matching_orders):
    """Renders the comprehensive 5-tab advanced quantitative data layout per iteration."""
    tab_equity, tab_analytics, tab_ledger, tab_raw, tab_mc = st.tabs([
        "Equity Curve & Summary", 
        "Trade Analytics & Returns Distribution", 
        "Strategy Experiment & Ledger", 
        "Raw CSV Inspector",
        "Monte Carlo Risk of Ruin"
    ])
    
    with tab_equity:
        eq_df = metrics.get("equity_curve")
        if isinstance(eq_df, pd.DataFrame) and not eq_df.empty:
            render_interactive_equity_chart(metrics, eq_df)
            
    with tab_analytics:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("##### Trade Distribution (Winners vs Losers)")
            win_c = metrics.get('winners', 0)
            lose_c = metrics.get('losers', 0)
            break_c = metrics.get('breakevens', 0)
            
            donut_data = pd.DataFrame({
                'Category': ['Winners', 'Losers', 'Breakevens'],
                'Count': [win_c, lose_c, break_c]
            })
            
            donut_chart = alt.Chart(donut_data).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(field="Count", type="quantitative"),
                color=alt.Color(field="Category", type="nominal", scale=alt.Scale(domain=['Winners', 'Losers', 'Breakevens'], range=['#00E676', '#FF5252', '#FFA726'])),
                tooltip=['Category', 'Count']
            ).properties(height=200)
            
            with st.container(border=True):
                st.altair_chart(donut_chart, width='stretch')

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
            entry_col = next((col for col in raw_df.columns if any(k in col.lower() for k in ['entry', 'start', 'open', 'time'])), None)
            exit_col = next((col for col in raw_df.columns if any(k in col.lower() for k in ['exit', 'end', 'close'])), None)
            pnl_col = next((col for col in raw_df.columns if any(k in col.lower() for k in ['profit', 'net', 'pnl', 'p&l'])), None)
            
            if entry_col and pnl_col:
                try:
                    chart_df = raw_df.copy()
                    chart_df['Entry_Time'] = pd.to_datetime(chart_df[entry_col], errors='coerce')
                    chart_df['Clean_PnL'] = pd.to_numeric(chart_df[pnl_col].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
                    
                    # Calculate overall average duration
                    avg_duration_str = "N/A"
                    if exit_col:
                        chart_df['Exit_Time'] = pd.to_datetime(chart_df[exit_col], errors='coerce')
                        durations = (chart_df['Exit_Time'] - chart_df['Entry_Time']).dt.total_seconds() / 60.0
                        avg_mins = durations.mean()
                        if not np.isnan(avg_mins):
                            if avg_mins >= 60:
                                avg_duration_str = f"{avg_mins / 60:.1f} hours"
                            else:
                                avg_duration_str = f"{avg_mins:.1f} mins"
                    
                    # Calculate separate Winner vs Loser durations & amounts
                    winning_trades = chart_df[chart_df['Clean_PnL'] > 0]
                    losing_trades = chart_df[chart_df['Clean_PnL'] < 0]
                    
                    def get_avg_dur(sub_df):
                        if sub_df.empty or not exit_col: return "N/A"
                        d = (sub_df['Exit_Time'] - sub_df['Entry_Time']).dt.total_seconds() / 60.0
                        m = d.mean()
                        if np.isnan(m): return "N/A"
                        return f"{m/60:.1f}h" if m >= 60 else f"{m:.1f}m"
                        
                    avg_win_dur = get_avg_dur(winning_trades)
                    avg_loss_dur = get_avg_dur(losing_trades)
                    
                    avg_win_amt = f"${winning_trades['Clean_PnL'].mean():,.2f}" if not winning_trades.empty else "$0.00"
                    avg_loss_amt = f"-${abs(losing_trades['Clean_PnL'].mean()):,.2f}" if not losing_trades.empty else "$0.00"
                    
                    # 1. CLEAN INSTITUTIONAL EXECUTIVE TEXT SUMMARY BAR
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
                            <div style="font-weight: 600; color: #94A3B8; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px;">📊 Execution Diagnostics</div>
                            <span style="margin-right: 15px;">⏱️ <b>Avg Duration:</b> {avg_duration_str}</span>
                            <span style="margin-right: 15px; color: #00E676;">🟢 <b>Avg Win Dur:</b> {avg_win_dur} ({avg_win_amt})</span>
                            <span style="color: #FF5252;">🔴 <b>Avg Loss Dur:</b> {avg_loss_dur} ({avg_loss_amt})</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # 2. Rolling Sharpe Ratio Overlay (Safeguarded window size)
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
                    st.warning(f"Could not generate temporal edge charts: {e}")
            else:
                st.info("Required timestamp and PnL columns not found for temporal analytics.")
                
    with tab_ledger:
        col_left, col_right = st.columns([1.5, 1])
        with col_left:
            with st.container(border=True):
                st.markdown("### Research Log & Experiment Notes")
                if md_path.exists():
                    st.markdown(cached_read_markdown(str(md_path)))
                else:
                    st.warning(f"Missing engineering log (`{md_path.name}`).")
                    
        with col_right:
            with st.container(border=True):
                st.markdown("### Performance Artifacts")
                st.write(f"**PDF Report:** `{base_name}.pdf`")
                st.write(f"**Storage:** Google Drive (Cloud)")
                
                # Fetch the dynamic Google Drive URL from backend metrics
                from backend_metrics import get_gdrive_pdf_url
                cloud_pdf_url = get_gdrive_pdf_url(base_name)
                
                if cloud_pdf_url != "#":
                    st.markdown(f"**[📥 Download Pristine 300 DPI PDF]({cloud_pdf_url})**")
                else:
                    st.warning("⚠️ Cloud PDF link pending registration.")

    with tab_raw:
        has_data = False
        if matching_trades and matching_trades.exists():
            has_data = True
            st.markdown(f"**Completed Trades Log (`{matching_trades.name}`):**")
            with st.container(border=True):
                st.dataframe(pd.read_csv(matching_trades, low_memory=False), width='stretch')
            
        if matching_orders and matching_orders.exists():
            has_data = True
            st.markdown(f"**Order Execution Fills Log (`{matching_orders.name}`):**")
            with st.container(border=True):
                st.dataframe(pd.read_csv(matching_orders, low_memory=False), width='stretch')
            
        if not has_data:
            st.info("No raw trades or orders CSV files found matching this iteration in reports/.")

    with tab_mc:
        render_monte_carlo_fragment(metrics, base_name)