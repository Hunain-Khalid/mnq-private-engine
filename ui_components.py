import streamlit as st
import pandas as pd
import altair as alt
from backend_metrics import cached_read_markdown, cached_read_file_bytes

def render_sidebar():
    """Renders the standard system sidebar configuration and returns selected page."""
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

@st.fragment
def render_interactive_equity_chart(metrics, eq_df):
    """Renders the clean single-color institutional equity curve, starting equity baseline, and 12-metric grid with percentages."""
    
    st.markdown("""
        <style>
            [data-testid="stMetricValue"] {
                font-size: 22px !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 13px !important;
            }
        </style>
    """, unsafe_allow_html=True)

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
    st.altair_chart(chart, width='stretch')

    eq_series = eq_df['Equity']
    start_val = eq_series.iloc[0]
    end_val = eq_series.iloc[-1]
    peak_val = eq_series.max()
    trough_val = eq_series.min()
    net_pnl = end_val - start_val
    
    # Calculate dollar drop and % drop for max drawdown
    max_dd_val = peak_val - trough_val
    max_dd_pct = (max_dd_val / peak_val) * 100 if peak_val > 0 else 0.0
    
    win_cnt = metrics.get('winners', 0)
    loss_cnt = metrics.get('losers', 0)
    
    # Parse raw trade numbers for Avg Win/Loss percentages
    raw_trades_df = metrics.get("raw_trades")
    avg_win_val = 0.0
    avg_loss_val = 0.0
    if isinstance(raw_trades_df, pd.DataFrame) and not raw_trades_df.empty:
        pnl_col = next((col for col in raw_trades_df.columns if any(k in col.lower() for k in ['profit', 'net', 'pnl', 'p&l', 'return', 'gain'])), None)
        if pnl_col:
            clean_pnl = pd.to_numeric(
                raw_trades_df[pnl_col].astype(str).str.replace('$', '').str.replace(',', ''), 
                errors='coerce'
            )
            avg_win_val = clean_pnl[clean_pnl > 0].mean() if win_cnt > 0 else 0.0
            avg_loss_val = abs(clean_pnl[clean_pnl < 0].mean()) if loss_cnt > 0 else 0.0

    avg_win_pct = (avg_win_val / start_val) * 100 if start_val > 0 else 0.0
    avg_loss_pct = (avg_loss_val / start_val) * 100 if start_val > 0 else 0.0
    raw_max_dd_str = metrics.get("max_drawdown", "31.7%")

    # ==========================================
    # 🏛️ 12-METRIC INSTITUTIONAL QUANT GRID (Percentages Added)
    # ==========================================
    
    # Row 1: Core Return & Risk-Adjusted Metrics (With Max DD Dollar & % breakdown)
    r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
    r1_c1.metric("Sharpe Ratio", metrics.get("sharpe", "N/A"))
    r1_c2.metric("Profit Factor", metrics.get("profit_factor", "N/A"))
    r1_c3.metric("Max Drawdown", f"{raw_max_dd_str} (-${max_dd_val:,.0f})")
    r1_c4.metric("Win Rate", metrics.get("win_rate", "N/A"))

    # Row 2: Trade Execution & Size Metrics (With Avg Win/Loss Percentages)
    r2_c1, r2_c2, r2_c3, r2_c4 = st.columns(4)
    r2_c1.metric("Total Trades", metrics.get("total_trades", "N/A"))
    r2_c2.metric("Avg Win", f"${avg_win_val:,.2f} (+{avg_win_pct:.2f}%)" if win_cnt > 0 else "$0.00")
    r2_c3.metric("Avg Loss", f"-${avg_loss_val:,.2f} (-{avg_loss_pct:.2f}%)" if loss_cnt > 0 else "$0.00")
    r2_c4.metric("W / L", f"{win_cnt}W / {loss_cnt}L")

    # Row 3: Portfolio Capital & Watermark Metrics
    r3_c1, r3_c2, r3_c3, r3_c4 = st.columns(4)
    r3_c1.metric("Net P&L", f"${net_pnl:,.0f}", delta=f"{(net_pnl/start_val)*100:.1f}%")
    r3_c2.metric("High Watermark (Peak)", f"${peak_val:,.0f}")
    r3_c3.metric("Max Trough", f"${trough_val:,.0f}")
    r3_c4.metric("Ending Capital", f"${end_val:,.0f}")

def render_pro_tabs(metrics, md_path, pdf_path, base_name, matching_trades, matching_orders):
    """Renders the comprehensive 4-tab advanced quantitative data layout per iteration."""
    
    tab_equity, tab_analytics, tab_ledger, tab_raw = st.tabs([
        "Equity Curve & Summary", 
        "Trade Analytics & Returns Distribution", 
        "Strategy Experiment & Ledger",  # Renamed Tab!
        "Raw CSV Inspector"
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
                        x=alt.X('Clean_PnL:Q', bin=alt.Bin(maxbins=20), title='Trade P&L ($)'),
                        y=alt.Y('count()', title='Number of Trades'),
                        color=alt.Color(
                            'Outcome:N', 
                            scale=alt.Scale(domain=['Winner', 'Loser', 'Breakeven'], range=['#00E676', '#FF5252', '#FFA726']), 
                            legend=None
                        ),
                        tooltip=['Clean_PnL:Q', 'count()']
                    ).properties(height=200).interactive()
                    
                    st.altair_chart(hist_chart, width='stretch')

    with tab_ledger:
        col_left, col_right = st.columns([1.5, 1])
        with col_left:
            st.markdown("### Research Log & Experiment Notes")
            if md_path.exists():
                st.markdown(cached_read_markdown(str(md_path)))
            else:
                st.warning(f"Missing engineering log (`{md_path.name}`).")
        with col_right:
            st.markdown("### Performance Artifacts")
            pdf_size_kb = pdf_path.stat().st_size / 1024
            st.write(f"**PDF Report:** `{pdf_path.name}`")
            st.write(f"**Size:** `{pdf_size_kb:.1f} KB`")
            
            pdf_bytes = cached_read_file_bytes(str(pdf_path))
            download_clicked = st.download_button(
                label="Download Full PDF Report",
                data=pdf_bytes,
                file_name=pdf_path.name,
                mime="application/pdf",
                key=f"pdf_{base_name}"
            )
            
            if download_clicked:
                st.toast("Thanks for downloading the institutional report!")

    with tab_raw:
        has_data = False
        if matching_trades and matching_trades.exists():
            has_data = True
            st.markdown(f"**Completed Trades Log (`{matching_trades.name}`):**")
            st.dataframe(pd.read_csv(matching_trades), width='stretch')
            
        if matching_orders and matching_orders.exists():
            has_data = True
            st.markdown(f"**Order Execution Fills Log (`{matching_orders.name}`):**")
            st.dataframe(pd.read_csv(matching_orders), width='stretch')
            
        if not has_data:
            st.info("No raw trades or orders CSV files found matching this iteration in reports/.")