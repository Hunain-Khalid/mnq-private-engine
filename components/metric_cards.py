import streamlit as st

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