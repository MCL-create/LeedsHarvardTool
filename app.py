import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from docx.shared import Pt
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# --- 1. MANDATORY INITIALIZATION ---
if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []
if 'audit_results' not in st.session_state:
    st.session_state.audit_results = None

# --- 2. MCL BRANDED THEME (#e6f7f8 background, #009688 buttons) ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="wide")
st.markdown(f"""
    <style>
    .stApp {{ background-color: #e6f7f8; color: #37474f; }}
    .stTabs [aria-selected="true"] {{ background-color: #009688 !important; color: white !important; }}
    div.stButton > button {{ background-color: #009688; color: white; border-radius: 5px; font-weight: bold; width: 100%; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. HEADER RESTORATION ---
header_file = "assets/HeadernoSQA.jpg"
if os.path.exists(header_file):
    st.image(header_file, use_column_width=True)

# --- 4. TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Essay Audit"])

# (Standard forms for Tabs 1-4 omitted for brevity)

# --- TAB 5: ADVANCED AUDIT WITH FEEDBACK ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx", key="mcl_master_uploader")
    
    if uploaded_file:
        if st.button("Run Full MCL Audit"):
            doc_input = Document(uploaded_file)
            bib_text = " ".join(st.session_state.bibliography).lower()
            results = []
            
            for i, para in enumerate(doc_input.paragraphs):
                # Regex for Leeds Harvard (Author, Year)
                found_cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', para.text)
                
                for c in found_cites:
                    surname = c.split(',')[0].split(' ')[0].lower()
                    matched = surname in bib_text
                    
                    # Feedback Logic 
                    has_quote = '"' in para.text or "'" in para.text
                    needs_page = "p." not in c.lower() and has_quote
                    
                    status = "✅ Matched" if matched else "⚠️ Missing"
                    feedback = "Formatting looks correct."
                    if not matched:
                        feedback = "Check spelling or ensure this is in your bibliography."
                    if needs_page:
                        feedback = "Quote detected: Add a page number (e.g., p.10)."

                    results.append({"Location": f"Para {i+1}", "Citation": f"({c})", "Status": status, "Feedback": feedback})

            # --- WORD REPORT WITH HEADER & APTOS FONT ---
            report_doc = Document()
            if os.path.exists(header_file):
                report_doc.add_picture(header_file, width=Pt(450))
            
            report_doc.add_heading('MCL Citation Audit Report', 0)
            style = report_doc.styles['Normal']
            style.font.name = 'Aptos'
            style.font.size = Pt(11)

            # Table Generation [cite: 105]
            table = report_doc.add_table(rows=1, cols=4)
            table.style = 'Table Grid'
            hdr = table.rows[0].cells
            hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = 'Loc', 'Citation', 'Status', 'Feedback'

            for res in results:
                row = table.add_row().cells
                row[0].text, row[1].text, row[2].text, row[3].text = res['Location'], res['Citation'], res['Status'], res['Feedback']

            buf = BytesIO()
            report_doc.save(buf)
            st.session_state.audit_results = results
            st.session_state.report_docx = buf.getvalue()

    if st.session_state.audit_results:
        st.table(st.session_state.audit_results)
        st.download_button("📥 Download Branded Audit Report (.docx)", st.session_state.report_docx, "MCL_Audit_Report.docx")
