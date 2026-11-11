import streamlit as st
from ui_styles import inject_global_institutional_theme

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