import streamlit as st
from backend_metrics import cached_read_markdown, get_gdrive_pdf_url

def render_ledger_tab(md_path, base_name):
    col_left, col_right = st.columns([1.5, 1])
    with col_left:
        with st.container(border=True):
            st.markdown("### Research Log & Experiment Notes")
            if md_path.exists():
                st.markdown(cached_read_markdown(str(md_path)))
            else:
                st.warning(f"Missing engineering log (`{md_path.name}`).")
                
    with col_right:
        with st.container(border=True):
            st.markdown("### Performance Artifacts")
            st.write(f"**PDF Report:** `{base_name}.pdf`")
            st.write(f"**Storage:** Google Drive (Cloud)")
            
            cloud_pdf_url = get_gdrive_pdf_url(base_name)
            
            if cloud_pdf_url != "#":
                st.markdown(f"**[📥 Download Pristine 300 DPI PDF]({cloud_pdf_url})**")
            else:
                st.warning("⚠️ Cloud PDF link pending registration.")