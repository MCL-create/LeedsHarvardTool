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
    .stTabs [aria-selected="true"] {{ background-color: #009688 !important; color: white !important; }}
    div.stButton > button {{ background-color: #009688; color: white; border-radius: 5px; font-weight: bold; width: 100%; }}
    .mcl-explanation {{ background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 8px solid #f9a825; margin: 20px 0; }}
    .success-card {{ background-color: #d4edda; color: #155724; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #c3e6cb; }}
    .audit-row {{ padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; }}
    </style>
""", unsafe_allow_html=True)

if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []

# --- 2. HEADER ---
img_path = "assets/Header.png"
if os.path.exists(img_path):
    st.image(img_path, use_column_width=True)

# --- 3. TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Essay Audit"
])

# --- TAB 1: BOOK ---
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
        
        # Download as Word Doc
        doc = Document()
        doc.add_heading('Bibliography', 0)
        for ref in st.session_state.bibliography:
            doc.add_paragraph(ref)
        
        buf = BytesIO()
        doc.save(buf)
        st.download_button("📥 Download Bibliography (.docx)", buf.getvalue(), "MCL_Bibliography.docx", key="dl_bib")
        
        if st.button("Clear All References", key="clear_bib"):
            st.session_state.bibliography = []
            st.rerun()

# --- TAB 5: ADVANCED AUDIT WITH LOCATIONS ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx", key="mcl_audit_loc")
    
    if uploaded_file and st.button("Run Audit", key="run_audit_v3"):
        doc = Document(uploaded_file)
        bib_low = " ".join(st.session_state.bibliography).lower()
        results = []
        report_lines = ["MCL ADVANCED AUDIT REPORT", "="*30, ""]
        
        # Iterate through paragraphs to find locations
        for i, para in enumerate(doc.paragraphs):
            # Regex to find citations in (Name, Year) format
            found_cites = re.findall(r'\(([^)]{5,100}?\d{4}[^)]{0,20}?)\)', para.text)
            
            for c in found_cites:
                surname = c.split(',')[0].split(' ')[0].lower()
                matched = surname in bib_low
                status = "✅ Matched" if matched else "⚠️ Missing"
                
                # Record result with Paragraph Location
                results.append({
                    "Location": f"Paragraph {i+1}",
                    "Citation": f"({c})",
                    "Status": status
                })
                
                report_lines.append(f"[{status}] {f'({c})':<40} | Location: Paragraph {i+1}")

        if results:
            st.table(results)
            
            # THE DOWNLOADABLE REPORT (Enhanced with locations)
            full_report = "\n".join(report_lines)
            st.download_button("📥 Download Detailed Report", full_report, "MCL_Detailed_Audit.txt")
            
            # --- SUCCESS CHECK ---
            if all(r["Status"] == "✅ Matched" for r in results):
                st.balloons()
                st.success("Perfect! Every citation matches your bibliography.")
        else:
            st.info("No citations detected in this document.")
