import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from docx.shared import Pt
import leeds_harvard_tool as lht

# --- 1. INITIALIZATION & STATE ---
if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []
if 'audit_results' not in st.session_state:
    st.session_state.audit_results = None

# --- 2. MCL BRANDED THEME ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="wide")
st.markdown(f"""
    <style>
    .stApp {{ background-color: #e6f7f8; color: #37474f; }}
    .stTabs [aria-selected="true"] {{ background-color: #009688 !important; color: white !important; }}
    div.stButton > button {{ background-color: #009688; color: white; border-radius: 5px; font-weight: bold; width: 100%; }}
    .report-card {{ background-color: #ffffff; padding: 20px; border-radius: 10px; border-left: 8px solid #f9a825; margin-bottom: 20px; }}
    </style>
""", unsafe_allow_html=True)

# --- 3. BRANDED HEADER ---
header_path = "assets/Header.png"
if os.path.exists(header_path):
    st.image(header_path, use_column_width=True)

# --- 4. TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Essay Audit"])

# --- TAB 1: BOOK (MAGIC FILL) ---
with tab1:
    st.header("Book Reference")
    with st.expander("✨ Magic Fill: Search by Title"):
        query = st.text_input("Enter Book Title", key="book_search")
        if query:
            matches = lht.search_books(query)
            if matches:
                choice = st.selectbox("Select match:", [m['label'] for m in matches])
                if st.button("Use Book Data"):
                    selected = next(m for m in matches if m['label'] == choice)
                    st.session_state.k_b_auth = selected['authors']
                    st.session_state.k_b_yr = selected['year']
                    st.session_state.k_b_tit = selected['title']
                    st.session_state.k_b_pub = selected['publisher']
    
    with st.form("book_form", clear_on_submit=True):
        auth = st.text_input("Authors", key="k_b_auth", value=st.session_state.get('k_b_auth', ''))
        yr = st.text_input("Year", key="k_b_yr", value=st.session_state.get('k_b_yr', ''))
        tit = st.text_input("Title", key="k_b_tit", value=st.session_state.get('k_b_tit', ''))
        ed = st.text_input("Edition (e.g. 2nd)")
        pub = st.text_input("Publisher", key="k_b_pub", value=st.session_state.get('k_b_pub', ''))
        if st.form_submit_button("Add to Bibliography"):
            st.session_state.bibliography.append(lht.generate_book_reference(auth, yr, tit, pub, ed))
            st.success("Reference Added!")

# --- TAB 2: JOURNAL (MAGIC FILL) ---
with tab2:
    st.header("Journal Reference")
    with st.expander("✨ Magic Fill: Search by Article Title"):
        j_query = st.text_input("Enter Article Title", key="j_search")
        if j_query:
            j_matches = lht.search_journals(j_query)
            if j_matches:
                j_choice = st.selectbox("Select match:", [m['label'] for m in j_matches])
                if st.button("Use Journal Data"):
                    sel = next(m for m in j_matches if m['label'] == j_choice)
                    st.session_state.k_j_auth = sel['authors']; st.session_state.k_j_yr = sel['year']
                    st.session_state.k_j_art_tit = sel['title']; st.session_state.k_j_jou_tit = sel['journal']

    with st.form("journal_form", clear_on_submit=True):
        j_auth = st.text_input("Authors", key="k_j_auth", value=st.session_state.get('k_j_auth', ''))
        j_yr = st.text_input("Year", key="k_j_yr", value=st.session_state.get('k_j_yr', ''))
        a_tit = st.text_input("Article Title", key="k_j_art_tit", value=st.session_state.get('k_j_art_tit', ''))
        j_tit = st.text_input("Journal Title", key="k_j_jou_tit", value=st.session_state.get('k_j_jou_tit', ''))
        v = st.text_input("Volume"); i = st.text_input("Issue"); p = st.text_input("Pages")
        if st.form_submit_button("Add to Bibliography"):
            st.session_state.bibliography.append(lht.generate_journal_reference(j_auth, j_yr, a_tit, j_tit, v, i, p))
            st.success("Reference Added!")

# --- TAB 3: WEBSITE (MAGIC FILL) ---
with tab3:
    st.header("Website Reference")
    with st.expander("✨ Magic Fill: Auto-Fill from URL"):
        w_url_input = st.text_input("Paste URL (e.g. SSSC or Gov.scot)")
        if st.button("Fetch Metadata"):
            w_data = lht.scrape_website_metadata(w_url_input)
            st.session_state.k_w_tit = w_data['title']; st.session_state.k_w_yr = w_data['year']
            st.session_state.k_w_url = w_url_input

    with st.form("web_form", clear_on_submit=True):
        w_auth = st.text_input("Author/Organization")
        w_yr = st.text_input("Year", value=st.session_state.get('k_w_yr', ''))
        w_tit = st.text_input("Page Title", value=st.session_state.get('k_w_tit', ''))
        w_url = st.text_input("URL", value=st.session_state.get('k_w_url', ''))
        w_acc = st.text_input("Date Accessed (e.g. 13 Jan 2026)")
        if st.form_submit_button("Add to Bibliography"):
            st.session_state.bibliography.append(lht.generate_website_reference(w_auth, w_yr, w_tit, w_url, w_acc))
            st.success("Reference Added!")

# --- TAB 4: BIBLIOGRAPHY ---
with tab4:
    st.header("Your Bibliography")
    st.session_state.bibliography.sort(key=lht.get_sort_key)
    for ref in st.session_state.bibliography:
        st.write(ref)
    if st.button("Clear Bibliography"):
        st.session_state.bibliography = []
        st.rerun()

# --- TAB 5: AUDIT (BRANDED + FEEDBACK) ---
with tab5:
    st.header("🔍 Essay Audit")
    uploaded = st.file_uploader("Upload Essay (.docx)", type="docx")
    if uploaded:
        if st.button("Run Full MCL Audit"):
            doc = Document(uploaded)
            bib_low = " ".join(st.session_state.bibliography).lower()
            results = []
            for i, p in enumerate(doc.paragraphs):
                # Regex looks for (Name, 2024)
                cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', p.text)
                for c in cites:
                    name_part = c.split(',')[0].split(' ')[0].lower()
                    matched = name_part in bib_low
                    feedback = "Correct." if matched else "Check bibliography."
                    # Scottish Social Care Logic
                    if any(x in c.lower() for x in ["sssc", "scottish", "standards"]):
                        feedback += " (Legislative source detected)."
                    if '"' in p.text and "p." not in c.lower():
                        feedback = "Direct quote detected: Needs page number (p.X)."
                    results.append({"Para": i+1, "Citation": f"({c})", "Status": "✅" if matched else "⚠️", "Feedback": feedback})
            st.session_state.audit_results = results
            
            # Word Report Generation
            rep = Document()
            if os.path.exists(header_path): rep.add_picture(header_path, width=Pt(450))
            rep.add_heading("MCL Audit Report", 0)
            style = rep.styles['Normal']; style.font.name = 'Aptos'; style.font.size = Pt(11)
            t = rep.add_table(rows=1, cols=4); t.style = 'Table Grid'
            for idx, text in enumerate(["Para", "Citation", "Status", "Feedback"]): t.rows[0].cells[idx].text = text
            for res in results:
                row = t.add_row().cells
                row[0].text, row[1].text, row[2].text, row[3].text = str(res['Para']), res['Citation'], res['Status'], res['Feedback']
            b = BytesIO(); rep.save(b); st.session_state.report_docx = b.getvalue()

    if st.session_state.audit_results:
        st.table(st.session_state.audit_results)
        st.download_button("📥 Download Branded Report", st.session_state.report_docx, "MCL_Audit.docx")
