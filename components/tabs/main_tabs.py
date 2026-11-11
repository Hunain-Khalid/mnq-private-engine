import streamlit as st
from components.tabs.equity_tab import render_equity_tab
from components.tabs.analytics_tab import render_analytics_tab
from components.tabs.ledger_tab import render_ledger_tab
from components.tabs.raw_tab import render_raw_tab
from components.monte_carlo import render_monte_carlo_fragment

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
        render_equity_tab(metrics)
            
    with tab_analytics:
        render_analytics_tab(metrics)
                
    with tab_ledger:
        render_ledger_tab(md_path, base_name)

    with tab_raw:
        render_raw_tab(matching_trades, matching_orders)

    with tab_mc:
        render_monte_carlo_fragment(metrics, base_name)