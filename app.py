import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from docx.shared import Pt
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# --- 1. MANDATORY INITIALIZATION (Fixes the AttributeError) ---
# This code MUST run before any other logic to keep tabs working
if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []
if 'audit_results' not in st.session_state:
    st.session_state.audit_results = None
if 'report_docx' not in st.session_state:
    st.session_state.report_docx = None

# --- 2. MCL BRANDED THEME ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #e6f7f8; color: #37474f; }}
    .stTabs [aria-selected="true"] {{ background-color: #009688 !important; color: white !important; }}
    div.stButton > button {{ background-color: #009688; color: white; border-radius: 5px; font-weight: bold; width: 100%; }}
    .report-card {{ background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 8px solid #f9a825; margin: 20px 0; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. BRANDED HEADER ---
# Use the correct file name from your assets folder
img_path = "assets/HeadernoSQA.jpg" 
if os.path.exists(img_path):
    st.image(img_path, use_column_width=True)

# --- 4. TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Essay Audit"
])

# --- TAB 1: BOOK ---
with tab1:
    st.header("Book Reference")
    with st.form("book_form", clear_on_submit=True):
        auth = st.text_input("Authors (Surname, Initial)", key="k_b_auth")
        yr = st.text_input("Year", key="k_b_yr")
        tit = st.text_input("Title", key="k_b_tit")
        pub = st.text_input("Publisher", key="k_b_pub")
        if st.form_submit_button("Add Reference"):
            if auth and yr and tit:
                res = generate_book_reference([a.strip() for a in auth.split(",")], yr, tit, pub, "", "")
                st.session_state.bibliography.append(res)
                st.success("Book Reference Saved!")

# --- TAB 2: JOURNAL ---
with tab2:
    st.header("Journal Article Reference")
    with st.form("journal_form", clear_on_submit=True):
        j_auth = st.text_input("Authors", key="k_j_auth")
        j_yr = st.text_input("Year", key="k_j_yr")
        a_tit = st.text_input("Article Title", key="k_j_art_tit")
        j_tit = st.text_input("Journal Title", key="k_j_jou_tit")
        vol = st.text_input("Volume", key="k_j_vol")
        iss = st.text_input("Issue", key="k_j_iss")
        pgs = st.text_input("Pages", key="k_j_pgs")
        if st.form_submit_button("Add Journal Reference"):
            if j_auth and j_yr and a_tit:
                res = generate_journal_reference([a.strip() for a in j_auth.split(",")], j_yr, a_tit, j_tit, vol, iss, pgs)
                st.session_state.bibliography.append(res)
                st.success("Journal Reference Saved!")

# --- TAB 3: WEBSITE ---
with tab3:
    st.header("Website Reference")
    with st.form("web_form", clear_on_submit=True):
        w_auth = st.text_input("Author/Organization", key="k_w_auth")
        w_yr = st.text_input("Year", key="k_w_yr")
        w_tit = st.text_input("Page Title", key="k_w_tit")
        url = st.text_input("URL", key="k_w_url")
        acc = st.text_input("Date Accessed", key="k_w_acc")
        if st.form_submit_button("Add Website Reference"):
            if w_auth and w_yr and w_tit:
                res = generate_website_reference([a.strip() for a in w_auth.split(",")], w_yr, w_tit, url, acc)
                st.session_state.bibliography.append(res)
                st.success("Website Reference Saved!")

# --- TAB 4: BIBLIOGRAPHY ---
with tab4:
    st.header("Your Bibliography")
    if not st.session_state.bibliography:
        st.info("Your list is empty. Add references in the other tabs first!")
    else:
        st.session_state.bibliography.sort(key=get_sort_key)
        for i, ref in enumerate(st.session_state.bibliography):
            st.markdown(f"{i+1}. {ref}")
        
        # Download Bibliography as .docx
        doc = Document()
        doc.add_heading('Bibliography', 0)
        for ref in st.session_state.bibliography:
            doc.add_paragraph(ref)
        
        buf = BytesIO()
        doc.save(buf)
        st.download_button("📥 Download Bibliography (.docx)", buf.getvalue(), "MCL_Bibliography.docx", key="dl_bib")
        
        if st.button("Clear All References", key="clear_all"):
            st.session_state.bibliography = []
            st.rerun()

# --- TAB 5: ESSAY AUDIT ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx", key="audit_uploader")
    
    if uploaded_file:
        if st.button("Run Full MCL Audit"):
            doc_input = Document(uploaded_file)
            bib_text = " ".join(st.session_state.bibliography).lower()
            results = []
            
            for i, para in enumerate(doc_input.paragraphs):
                # Look for (Author, Year) or (Author, Year, p. X)
                found_cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', para.text)
                
                for c in found_cites:
                    surname = c.split(',')[0].split(' ')[0].lower()
                    matched = surname in bib_text
                    status = "✅ Matched" if matched else "⚠️ Missing"
                    
                    results.append({
                        "Location": f"Para {i+1}",
                        "Citation": f"({c})",
                        "Status": status
                    })

            # Prepare Word Report
            report_doc = Document()
            if os.path.exists(img_path):
                report_doc.add_picture(img_path, width=Pt(450))
            
            report_doc.add_heading('MCL Citation Audit Report', 0)
            
            # Use Aptos Font
            style = report_doc.styles['Normal']
            style.font.name = 'Aptos'
            style.font.size = Pt(11)

            table = report_doc.add_table(rows=1, cols=3)
            table.style = 'Table Grid'
            hdr = table.rows[0].cells
            hdr[0].text, hdr[1].text, hdr[2].text = 'Location', 'Citation', 'Status'

            for res in results:
                row = table.add_row().cells
                row[0].text, row[1].text, row[2].text = res['Location'], res['Citation'], res['Status']

            buf = BytesIO()
            report_doc.save(buf)
            st.session_state.audit_results = results
            st.session_state.report_docx = buf.getvalue()

    # Safely check if results exist before displaying
    if st.session_state.audit_results is not None:
        st.table(st.session_state.audit_results)
        st.download_button("📥 Download Branded Audit Report (.docx)", st.session_state.report_docx, "MCL_Audit_Report.docx")
