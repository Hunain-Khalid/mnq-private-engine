import streamlit as st

def inject_global_institutional_theme():
    """Injects global CSS for high-contrast institutional styling, white dividers, and conditional red/green cards."""
    st.markdown("""
        <style>
            /* 1. DEFAULT INSTITUTIONAL METRIC CARDS (Green accent, brighter border) */
            div[data-testid="stMetric"] {
                background-color: #121C24 !important;
                border: 1px solid #334155 !important;
                border-left: 4px solid #00E676 !important;
                padding: 14px 18px !important;
                border-radius: 8px !important;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
            }
            [data-testid="stMetricValue"] {
                font-size: 20px !important;
                color: #FFFFFF !important;
            }
            [data-testid="stMetricLabel"] {
                font-size: 12px !important;
                color: #94A3B8 !important;
            }

            /* 2. CONDITIONAL RED CARDS FOR NEGATIVE VALUES / DRAWDOWN WARNINGS */
            div[data-testid="stMetric"]:has(div[data-testid="stMetricValue"]:contains("-")),
            div[data-testid="stMetric"]:has(div[data-testid="stMetricDelta"] span[data-testid="stMetricDeltaIcon-down"]) {
                background-color: #2A1215 !important;
                border: 1px solid #7F1D1D !important;
                border-left: 4px solid #FF5252 !important;
            }

            /* 3. TARGET STREAMLIT'S NATIVE BORDERED CONTAINERS EXPLICITLY */
            [data-testid="stVerticalBlockBorderWrapper"] {
                border: 2px solid #64748B !important;
                border-radius: 12px !important;
                background-color: #121C24 !important;
            }
            
            /* Make negative metric values red */
            div[data-testid="stMetric"]:has(div[data-testid="stMetricValue"]:contains("-")) [data-testid="stMetricValue"] {
                color: #FF5252 !important;
            }

            /* 4. TOOLBAR CLEANUP */
            div[data-testid="stElementToolbar"] {
                background: transparent !important;
            }
            
            /* 5. CRISP INSTITUTIONAL WHITE/GREY GRADIENT DIVIDERS */
            hr {
                border: none !important;
                height: 2px !important;
                background: linear-gradient(90deg, #E2E8F0 0%, #1E293B 100%) !important;
                margin: 28px 0px !important;
            }
        </style>
    """, unsafe_allow_html=True)