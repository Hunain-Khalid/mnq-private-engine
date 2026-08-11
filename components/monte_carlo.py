import streamlit as st
import pandas as pd
import altair as alt
from backend_metrics import run_monte_carlo_simulation
from components.metric_cards import institutional_metric

@st.fragment
def render_monte_carlo_fragment(metrics, base_name):
    """Isolated Monte Carlo fragment with spaghetti paths, P5-P95 tail bounds, and drawdown histogram."""
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