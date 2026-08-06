import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Alpha Flush Strategy Gallery", layout="wide")

# Master Navigation Switch in the Sidebar
st.sidebar.title("🏛️ Alpha Flush Node")
page = st.sidebar.radio("Navigation", ["📊 Backtests (IS / OOS)", "🚀 Live / Paper Trading", "📜 Engineering Archive"])

if page == "📊 Backtests (IS / OOS)":
    st.title("📊 Quantitative Backtests & Validation")
    st.markdown("Here we track our In-Sample training runs versus blind Out-of-Sample (OOS) validation.")
    
    # Hero Section for Current Best
    st.subheader("🏆 Current Production Model: v1.2 (HMA + ATR)")
    st.info("This model passed the 6-month blind OOS test with a Sharpe > 1.5 and Max Drawdown < 12%.")
    
    # Render your reports logic here for Backtests...
    st.divider()
    st.subheader("📁 Backtest Archive")
    # Expander for older versions
    with st.expander("View Older Iterations"):
        st.write("Older PDF reports and logs render here...")

elif page == "🚀 Live / Paper Trading":
    st.title("🚀 Forward Testing & Live Paper Trading")
    st.markdown("Real-time forward testing results connected via Tradovate sandbox simulation.")
    
    # Placeholder for live metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Live Paper PnL", "+$1,240.00", "+4.2%")
    col2.metric("Execution Slippage", "0.25 pts", "Optimal")
    col3.metric("Live Win Rate", "62.5%", "Stable")
    
    st.line_chart([100000, 101000, 100500, 101240])

elif page == "📜 Engineering Archive":
    st.title("📜 Engineering Changelog & System Architecture")
    st.markdown("The chronological history of our infrastructure pivots, bugs, and lessons learned.")
    
    # Render full changelog history here...
    st.write("Changelog markdown renders here...")

st.title("🏛️ Alpha Flush Node: Strategy Evolution Gallery")
st.markdown("Systematic MNQ Trend-Following & Volatility-Gated Flush Strategy — Iterative Backtest Artifacts.")

reports_dir = Path("reports")

# Ensure reports directory exists
if not reports_dir.exists():
    reports_dir.mkdir()
    st.warning("⚠️ Created a 'reports/' folder. Drop your QC PDFs and matching .md logs in there!")

# Find all PDF reports (UN-INDENTED so it always runs!)
pdf_files = sorted(reports_dir.glob("*.pdf"), reverse=True) # Newest first

if not pdf_files:
    st.info("📁 No reports found yet. Add your QC PDFs and markdown logs to the `reports/` folder.")
else:
    st.subheader(f"📊 Strategy Iterations & Changelog ({len(pdf_files)} Versions Tracked)")

    for pdf_path in pdf_files:
        # Find the matching markdown file (e.g., v0.1 Baseline.pdf -> v0.1 Baseline.md)
        md_path = pdf_path.with_suffix(".md")

        with st.container():
            st.divider()

            # Create two columns: Left for the Engineering Log (.md), Right for the PDF artifact
            col_left, col_right = st.columns([1.5, 1])

            with col_left:
                st.markdown(f"### 🧪 Iteration: `{pdf_path.stem}`")

                if md_path.exists():
                    # Read and render the matching markdown file
                    with open(md_path, "r", encoding="utf-8") as f:
                        md_content = f.read()
                    st.markdown(md_content)
                else:
                    st.warning(f"⚠️ Missing engineering log (`{md_path.name}`). Create this file to document why this iteration was run!")

            # 🛠️ FIXED INDENTATION: Now correctly aligned outside col_left
            with col_right:
                st.markdown("### 📈 Performance Tear Sheet")
                st.write(f"**Artifact:** `{pdf_path.name}`")
                st.write(f"**Size:** {pdf_path.stat().st_size / 1024:.1f} KB")

                # PDF Download Button
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label=f"📥 Download PDF Report",
                        data=f,
                        file_name=pdf_path.name,
                        mime="application/pdf",
                        key=f"download_{pdf_path.name}"
                    )

# 🛠️ FIXED INDENTATION: Sidebar is now at the root level
st.sidebar.header("Pipeline Architecture")
st.sidebar.markdown("""
1. **Model:** QuantConnect Cloud (Python/LEAN)
2. **Obfuscation:** Git-ignored `params.json` (Variable mapping)
3. **Artifacts:** Compressed PDFs + Markdown Engineering Logs
4. **Hosting:** Streamlit Community Cloud
""")