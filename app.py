import streamlit as st
from ddr_engine import extract_text_from_pdf, generate_ddr_data
from report_builder import build_docx

st.set_page_config(
    page_title="DDR Report Generator",
    page_icon="🏗️",
    layout="centered"
)

# Clean header
st.markdown("""
    <h1 style='color:#1B3A6B; font-family:Arial;'>DDR Report Generator</h1>
    <p style='color:#595959; font-family:Arial;'>
        Upload your inspection documents to automatically generate a 
        Detailed Diagnostic Report.
    </p>
    <hr/>
""", unsafe_allow_html=True)

# Upload section
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Inspection Report**")
    inspection_file = st.file_uploader(
        "Upload PDF", type=["pdf"], key="inspection",
        label_visibility="collapsed"
    )
with col2:
    st.markdown("**Thermal Images Report**")
    thermal_file = st.file_uploader(
        "Upload PDF", type=["pdf"], key="thermal",
        label_visibility="collapsed"
    )

st.markdown("<hr/>", unsafe_allow_html=True)

if inspection_file and thermal_file:
    st.success("Both files uploaded successfully.")

    if st.button("Generate DDR Report", type="primary", use_container_width=True):

        progress = st.progress(0, text="Reading inspection report...")

        inspection_text = extract_text_from_pdf(inspection_file)
        progress.progress(25, text="Reading thermal data...")

        thermal_text = extract_text_from_pdf(thermal_file)
        progress.progress(50, text="Analysing documents...")

        try:
            ddr_data = generate_ddr_data(inspection_text, thermal_text)
            progress.progress(85, text="Building report document...")
        except Exception as e:
            progress.empty()
            st.error(f"Analysis failed: {str(e)}")
            st.stop()

        docx_bytes = build_docx(ddr_data)
        progress.progress(100, text="Complete.")
        progress.empty()

        st.success("Report generated successfully.")

        st.download_button(
            label="Download DDR Report (.docx)",
            data=docx_bytes,
            file_name="DDR_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

        # Clean summary preview
        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown("### Report Summary")

        data = ddr_data
        overview = data.get("property_summary", {}).get("overview", "")
        if overview:
            st.markdown(f"**Overview:** {overview}")

        severity_list = data.get("severity", [])
        if severity_list:
            st.markdown("**Severity Overview:**")
            for item in severity_list:
                level = item.get("level", "")
                indicator = {"High": "🔴", "Moderate": "🟡", "Low": "🟢"}.get(level, "⚪")
                st.markdown(
                    f"{indicator} &nbsp; **{item.get('area', '')}** — {level}",
                    unsafe_allow_html=True
                )

elif inspection_file or thermal_file:
    st.warning("Please upload both files to proceed.")
else:
    st.markdown("""
    **How to use:**
    1. Upload the Inspection Report PDF on the left
    2. Upload the Thermal Images PDF on the right
    3. Click Generate DDR Report
    4. Download the formatted Word document
    """)