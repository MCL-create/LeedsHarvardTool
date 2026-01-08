import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# --- 1. MCL BRANDED THEME ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="centered")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #e6f7f8; color: #37474f; }}
    .stTabs [aria-selected="true"] {{ 
        background-color: #009688 !important; 
        color: white !important; 
    }}
    /* Target buttons with MCL Deep Turquoise */
    div.stButton > button:first-child {{
        background-color: #009688;
        color: white;
        border-radius: 5px;
        border: none;
    }}
    /* Table styling for Audit results */
    [data-testid="stTable"] {{
        background-color: white;
        border-radius: 10px;
    }}
    </style>
""", unsafe_allow_html=True)

if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []

# --- 2. HEADER ---
img_path = "assets/Header.png"
if os.path.exists(img_path):
    st.image(img_path, use_column_width=True) # Compatible with Render environment

# --- 3. TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Essay Audit"
])

# [Tabs 1-4 logic remains as previously established for reference generation]

# --- TAB 5: RE-ACTIVATED ESSAY AUDIT ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    st.write("Check your in-text citations against your generated bibliography.")
    
    # Unique key 'mcl_essay_audit' prevents the widget from freezing
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx", key="mcl_essay_audit")
    
    if uploaded_file is not None:
        # Added a 'Process' button to trigger the analysis explicitly
        if st.button("Run Audit & Generate Report", key="run_audit_btn"):
            try:
                doc = Document(uploaded_file)
                # Join all text to find citations
                full_text = " ".join([p.text for p in doc.paragraphs])
                
                # Regex limits search to 100 characters to avoid catching full paragraphs
                cites = re.findall(r'\(([^)]{5,100}?\d{4}[^)]{0,20}?)\)', full_text)
                
                if cites:
                    st.subheader(f"Results: {len(cites)} Citations Detected")
                    bib_content = " ".join(st.session_state.bibliography).lower()
                    
                    audit_results = []
                    report_content = "MCL ESSAY AUDIT REPORT\n" + "="*25 + "\n\n"
                    
                    for c in sorted(list(set(cites))):
                        # Match the surname (first word) against the bibliography
                        surname = c.split(',')[0].split(' ')[0].lower()
                        is_matched = surname in bib_content
                        status = "✅ Matched" if is_matched else "⚠️ Missing"
                        
                        audit_results.append({"Citation": f"({c})", "Status": status})
                        report_content += f"[{status}] ({c})\n"
                    
                    st.table(audit_results)
                    
                    # --- DOWNLOAD FUNCTIONALITY ---
                    # MIME type 'text/plain' ensures compatibility across devices
                    st.download_button(
                        label="📥 Download Audit Report (.txt)",
                        data=report_content,
                        file_name="MCL_Audit_Report.txt",
                        mime="text/plain",
                        key="report_download_active"
                    )
                else:
                    st.warning("No citations detected. Please ensure your citations are in brackets, e.g., (Smith, 2024).")
            except Exception as e:
                st.error(f"Analysis error: {e}")

# --- FOOTER ---
st.markdown("---")
st.markdown(
    f"<div style='text-align: center; color: #37474f; font-size: 0.8em;'>"
    f"© 2026 Macmillan Centre for Learning. <br>"
    f"<a href='https://www.macmillancentreforlearning.co.uk/home-2/' target='_blank' style='color: #0288d1; font-weight: bold;'>Go to Macmillan Centre for Learning</a>"
    f"</div>", 
    unsafe_allow_html=True
)
