import streamlit as st
import pandas as pd

def render_raw_tab(matching_trades, matching_orders):
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