import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from docx.shared import Pt
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# --- 1. GLOBAL INITIALIZATION (Fixes Upload & Error Bugs) ---
if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []
if 'audit_results' not in st.session_state:
    st.session_state.audit_results = None

# --- 2. MCL BRANDED THEME (Using Macmillan Colours Table) ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #e6f7f8; color: #37474f; }} /* Background & Text  */
    .stTabs [aria-selected="true"] {{ background-color: #009688 !important; color: white !important; }} /* Button BG  */
    div.stButton > button {{ background-color: #009688; color: white; border-radius: 5px; font-weight: bold; width: 100%; }}
    .report-card {{ background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 8px solid #f9a825; margin: 20px 0; }} /* Accent Colour  */
    </style>
""", unsafe_allow_html=True)

# --- 3. BRANDED HEADER ---
if os.path.exists("assets/Header.png"):
    st.image("assets/Header.png", use_column_width=True)

# --- 4. TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Essay Audit"])

# [Tabs 1-3 contain the standard entry forms linked to generate_functions]

# --- TAB 5: ADVANCED BRANDED AUDIT ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx", key="final_audit_uploader")
    
    if uploaded_file:
        if st.button("Run Full MCL Audit"):
            doc_input = Document(uploaded_file)
            bib_text = " ".join(st.session_state.bibliography).lower()
            results = []
            
            for i, para in enumerate(doc_input.paragraphs):
                # Advanced Regex for Leeds Harvard (Author, Year) or (Author, Year, p. X)
                found_cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', para.text)
                
                for c in found_cites:
                    # 1. Legislative/Corporate Check (Scottish Nuance)
                    is_legislative = any(word in c.lower() for word in ["sssc", "scottish", "standards", "act"])
                    
                    # 2. Match Logic
                    surname = c.split(',')[0].split(' ')[0].lower()
                    matched = surname in bib_text
                    
                    # 3. Quote Check (Leeds Harvard Requirement) [cite: 41, 48]
                    has_quote = '"' in para.text or "'" in para.text
                    needs_page = "p." not in c.lower() and has_quote
                    
                    status = "✅ Matched" if matched else "⚠️ Missing"
                    feedback = "Formatting looks correct."
                    if not matched:
                        feedback = "Check spelling or ensure this is added to your bibliography."
                    if needs_page:
                        feedback = "Direct quote detected. Leeds Harvard requires a page number (e.g., p. 10)."

                    results.append({
                        "Location": f"Para {i+1}",
                        "Citation": f"({c})",
                        "Status": status,
                        "Suggestions": feedback
                    })

            # --- GENERATE BRANDED WORD REPORT ---
            report_doc = Document()
            # Add MCL Header to Word
            if os.path.exists("assets/Header.png"):
                report_doc.add_picture("assets/Header.png", width=Pt(450))
            
            report_doc.add_heading('MCL Citation Audit Report', 0)
            
            # Set Aptos Font [Requested Amendment]
            style = report_doc.styles['Normal']
            style.font.name = 'Aptos'
            style.font.size = Pt(11)

            # Audit Table in Word
            table = report_doc.add_table(rows=1, cols=4)
            table.style = 'Table Grid'
            hdr = table.rows[0].cells
            hdr[0].text, hdr[1].text, hdr[2].text, hdr[3].text = 'Loc', 'Citation', 'Status', 'Feedback'

            for res in results:
                row = table.add_row().cells
                row[0].text, row[1].text, row[2].text, row[3].text = res['Location'], res['Citation'], res['Status'], res['Suggestions']

            buf = BytesIO()
            report_doc.save(buf)
            st.session_state.audit_results = results
            st.session_state.report_docx = buf.getvalue()

    if st.session_state.audit_results:
        st.table(st.session_state.audit_results)
        st.download_button("📥 Download Branded Audit Report (.docx)", st.session_state.report_docx, "MCL_Audit_Report.docx")
