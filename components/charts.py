import streamlit as st
import pandas as pd
import altair as alt

def render_interactive_equity_chart(eq_df):
    """Renders the clean single-color institutional equity curve and starting equity baseline."""
    try:
        min_idx = eq_df.index.min()
        max_idx = eq_df.index.max()
        start_date_str = min_idx.strftime('%Y-%m-%d') if hasattr(min_idx, 'strftime') else str(min_idx)
        end_date_str = max_idx.strftime('%Y-%m-%d') if hasattr(max_idx, 'strftime') else str(max_idx)
    except Exception:
        start_date_str = "N/A"
        end_date_str = "N/A"
    
    st.markdown(f"**Backtest Date Range:** `{start_date_str}` ➔ `{end_date_str}`")

    start_cap_val = eq_df['Equity'].iloc[0]
    
    x_col = 'Time:T' if 'Time' in eq_df.index.name or isinstance(eq_df.index, pd.DatetimeIndex) else 'Trade_Index:Q'
    x_title = 'Timeline (Trade Exit Date)' if x_col == 'Time:T' else 'Trade Sequence Index'

    line = alt.Chart(eq_df.reset_index()).mark_line(
        color='#00E676', strokeWidth=2.2
    ).encode(
        x=alt.X(x_col, title=x_title),
        y=alt.Y('Equity:Q', scale=alt.Scale(zero=False), title='Account Equity ($)'),
        tooltip=[x_col, 'Equity:Q']
    )
    
    baseline_rule = alt.Chart(pd.DataFrame({'y': [start_cap_val]})).mark_rule(
        color='#FFA726', strokeDash=[4, 4], strokeWidth=1.5
    ).encode(y='y:Q')
    
    chart = (line + baseline_rule).properties(height=220).interactive()
    st.caption("Dashed Line: Starting Equity Baseline ($1,000,000)")
    
    with st.container(border=True):
        st.altair_chart(chart, width='stretch')