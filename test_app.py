import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Alpha Flush Strategy Gallery", layout="wide")

st.title("🏛️ Alpha Flush Node: Strategy Evolution Gallery")
st.markdown("Systematic MNQ Trend-Following & Volatility-Gated Flush Strategy — Iterative Backtest Artifacts.")

reports_dir = Path("reports")

if not reports_dir.exists():
    reports_dir.mkdir()
    st.warning("⚠️ Created a 'reports/' folder. Drop your QC PDFs and matching .md logs in there!")

    # Find all PDF reports
    pdf_files = sorted(reports_dir.glob("*.pdf"), reverse=True) # Newest first

    if not pdf_files:
        st.info("📁 No reports found yet. Add your QC PDFs and markdown logs to the `reports/` folder.")
    else:
        st.subheader(f"📊 Strategy Iterations & Changelog ({len(pdf_files)} Versions Tracked)")

        for pdf_path in pdf_files:
            # Find the matching markdown file (e.g., v1_baseline.pdf -> v1_baseline.md)
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

                                # Sidebar metadata
                                st.sidebar.header("Pipeline Architecture")
                                st.sidebar.markdown("""
                                1. **Model:** QuantConnect Cloud (Python/LEAN)
                                2. **Obfuscation:** Git-ignored `params.json` (Variable mapping)
                                3. **Artifacts:** Compressed PDFs + Markdown Engineering Logs
                                4. **Hosting:** Streamlit Community Cloud
                                """)