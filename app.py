import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from docx.shared import Pt
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# --- 1. INITIALIZE SESSION STATE (Fixes the AttributeError) ---
# This must be at the very top to prevent errors in other tabs
if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []
if 'audit_results' not in st.session_state:
    st.session_state.audit_results = None
if 'report_docx' not in st.session_state:
    st.session_state.report_docx = None
if 'missing_count' not in st.session_state:
    st.session_state.missing_count = 0

# --- 2. MCL BRANDED THEME ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="centered")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #e6f7f8; color: #37474f; }}
    .stTabs [aria-selected="true"] {{ background-color: #009688 !important; color: white !important; }}
    div.stButton > button {{ background-color: #009688; color: white; border-radius: 5px; font-weight: bold; width: 100%; }}
    .mcl-explanation {{ background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 8px solid #f9a825; margin: 20px 0; }}
    .success-card {{ background-color: #d4edda; color: #155724; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #c3e6cb; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. HEADER (Fixes the TypeError) ---
img_path = "assets/Header.png"
if os.path.exists(img_path):
    # Changed from use_container_width to use_column_width to match your Streamlit version
    st.image(img_path, use_column_width=True)

# --- 4. TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Essay Audit"
])

# --- TAB 1, 2, 3 (References) ---
with tab1:
    st.header("Book Reference")
    with st.form("book_active", clear_on_submit=True):
        auth = st.text_input("Authors (Surname, Initial)", key="k_b_auth")
        yr = st.text_input("Year", key="k_b_yr")
        tit = st.text_input("Title", key="k_b_tit")
        pub = st.text_input("Publisher", key="k_b_pub")
        if st.form_submit_button("Add Reference"):
            if auth and yr and tit:
                res = generate_book_reference([a.strip() for a in auth.split(",")], yr, tit, pub, "", "")
                st.session_state.bibliography.append(res)
                st.success("Book Reference Saved!")

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
        
        doc = Document()
        doc.add_heading('Bibliography', 0)
        for ref in st.session_state.bibliography:
            doc.add_paragraph(ref)
        
        buf = BytesIO()
        doc.save(buf)
        st.download_button("📥 Download Bibliography (.docx)", buf.getvalue(), "MCL_Bibliography.docx", key="dl_bib")
        
        if st.button("Clear All References", key="clear_bib"):
            st.session_state.bibliography = []
            st.session_state.audit_results = None # Clear audit too
            st.rerun()
# --- TAB 5: ADVANCED AUDIT (STABLE UPLOAD VERSION) ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    
    # Using a clear instruction and unique key for the uploader
    uploaded_file = st.file_uploader(
        "Upload Essay (.docx)", 
        type="docx", 
        key="mcl_audit_uploader_unique"
    )
    
    if uploaded_file is not None:
        # Provide visual feedback that the file is ready
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        
        if st.button("Run Audit & Generate Report", key="run_audit_btn"):
            try:
                # Re-read the file into the Document object
                doc_input = Document(uploaded_file)
                bib_low = " ".join(st.session_state.bibliography).lower()
                results = []
                missing_count = 0
                
                # Process Audit
                for i, para in enumerate(doc_input.paragraphs):
                    found_cites = re.findall(r'\(([^)]{5,100}?\d{4}[^)]{0,20}?)\)', para.text)
                    for c in found_cites:
                        # Extract first word of citation (usually author)
                        surname = c.split(',')[0].split(' ')[0].lower()
                        matched = surname in bib_low
                        if not matched: missing_count += 1
                        status = "✅ Matched" if matched else "⚠️ Missing"
                        results.append({"Location": f"Paragraph {i+1}", "Citation": f"({c})", "Status": status})

                if results:
                    # Generate the Branded Word Report
                    report_doc = Document()
                    if os.path.exists("assets/Header.png"):
                        report_doc.add_picture("assets/Header.png", width=Pt(450))
                    
                    report_doc.add_heading('Essay Citation Audit Report', 0)
                    
                    # Apply Font Style
                    style = report_doc.styles['Normal']
                    style.font.name = 'Aptos'
                    style.font.size = Pt(11)

                    report_doc.add_paragraph(f"Audit Summary: {len(results) - missing_count} matches found.")

                    # Build Table
                    table = report_doc.add_table(rows=1, cols=3)
                    table.style = 'Table Grid'
                    hdr_cells = table.rows[0].cells
                    hdr_cells[0].text, hdr_cells[1].text, hdr_cells[2].text = 'Location', 'Citation', 'Status'

                    for item in results:
                        row = table.add_row().cells
                        row[0].text, row[1].text, row[2].text = item['Location'], item['Citation'], item['Status']

                    buf = BytesIO()
                    report_doc.save(buf)
                    
                    # Store results so they persist
                    st.session_state.audit_results = results
                    st.session_state.report_docx = buf.getvalue()
                    st.session_state.missing_count = missing_count
                else:
                    st.warning("No citations detected in the format (Author, Year).")

            except Exception as e:
                st.error(f"Error processing document: {e}")

    # Display Persistent Results
    if st.session_state.audit_results is not None:
        st.subheader(f"Results: {len(st.session_state.audit_results)} Citations Detected")
        st.table(st.session_state.audit_results)
        
        st.download_button(
            label="📥 Download Branded Audit Report (.docx)",
            data=st.session_state.report_docx,
            file_name="MCL_Audit_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
