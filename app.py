import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# --- 1. PAGE CONFIG & MCL THEME ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="centered")

# Custom CSS for MCL Blue Theme
st.markdown("""
    <style>
    .stTabs [aria-selected="true"] { background-color: #004a99 !important; color: white !important; }
    div.stButton > button:first-child { background-color: #004a99; color: white; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []

# --- 2. FIXED HEADER LOGIC ---
# Using 'use_column_width' as requested by the server error log
img_path = "assets/Header.png"

if os.path.exists(img_path):
    st.image(img_path, use_column_width=True)
else:
    st.title("📚 MCL Leeds Harvard Pro Tool")

# --- 3. TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 Book", "📰 Journal Article", "🌐 Website", "📋 My Bibliography", "🔍 Essay Audit"
])

# --- TAB 1: BOOK ---
with tab1:
    st.header("Book Reference")
    with st.form("book_form"):
        authors = st.text_input("Authors (comma separated)", placeholder="e.g. Smith, J., Doe, R.")
        year = st.text_input("Year of Publication")
        title = st.text_input("Book Title")
        edition = st.text_input("Edition (leave blank if 1st)")
        place = st.text_input("Place of Publication")
        publisher = st.text_input("Publisher")
        if st.form_submit_button("Generate & Add to List"):
            if authors and year and title:
                res = generate_book_reference([a.strip() for a in authors.split(",")], year, title, publisher, place, edition)
                st.session_state.bibliography.append(res)
                st.success("Reference added!")

# --- TAB 2: JOURNAL ---
with tab2:
    st.header("Journal Reference")
    with st.form("journal_form"):
        j_auth = st.text_input("Authors")
        j_yr = st.text_input("Year")
        a_tit = st.text_input("Article Title")
        j_tit = st.text_input("Journal Title")
        vol = st.text_input("Volume")
        iss = st.text_input("Issue")
        pgs = st.text_input("Pages")
        if st.form_submit_button("Generate & Add"):
            res = generate_journal_reference([a.strip() for a in j_auth.split(",")], j_yr, a_tit, j_tit, vol, iss, pgs)
            st.session_state.bibliography.append(res)
            st.success("Reference added!")

# --- TAB 3: WEBSITE ---
with tab3:
    st.header("Website Reference")
    with st.form("web_form"):
        w_auth = st.text_input("Author/Org")
        w_yr = st.text_input("Year")
        w_tit = st.text_input("Page Title")
        url = st.text_input("URL")
        acc = st.text_input("Date Accessed")
        if st.form_submit_button("Generate & Add"):
            res = generate_website_reference([a.strip() for a in w_auth.split(",")], w_yr, w_tit, url, acc)
            st.session_state.bibliography.append(res)
            st.success("Reference added!")

# --- TAB 4: BIBLIOGRAPHY ---
with tab4:
    st.header("Final Bibliography")
    if not st.session_state.bibliography:
        st.info("Your list is empty.")
    else:
        st.session_state.bibliography.sort(key=get_sort_key)
        for ref in st.session_state.bibliography:
            st.markdown(f"- {ref}")
        
        doc = Document()
        doc.add_heading('Bibliography', 0)
        for ref in st.session_state.bibliography:
            p = doc.add_paragraph()
            parts = ref.split('*')
            for i, pt in enumerate(parts):
                run = p.add_run(pt)
                if i % 2 != 0: run.italic = True
        
        buf = BytesIO()
        doc.save(buf)
        st.download_button("📥 Download Bibliography (.docx)", buf.getvalue(), "MCL_Bibliography.docx")

# --- TAB 5: ESSAY AUDIT & REPORT ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx")
    
    if uploaded_file:
        doc = Document(uploaded_file)
        full_text = " ".join([p.text for p in doc.paragraphs])
        citations_found = re.findall(r'\(([^)]{5,100}?\d{4}[^)]{0,20}?)\)', full_text)
        
        if citations_found:
            bib_joined = " ".join(st.session_state.bibliography).lower()
            audit_list = []
            report_text = "MCL REFERENCE AUDIT REPORT\n" + "="*30 + "\n\n"
            
            for cite in sorted(list(set(citations_found))):
                main_name = cite.split(',')[0].split(' ')[0].lower()
                status = "✅ Matched" if main_name in bib_joined else "⚠️ Missing"
                audit_list.append({"Citation": f"({cite})", "Status": status})
                report_text += f"[{status}] ({cite})\n"
            
            st.table(audit_list)
            st.download_button("📥 Download Report (.txt)", report_text, "MCL_Audit.txt")

# --- MCL FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey; font-size: 0.8em;'>"
    "© 2026 Macmillan Centre for Learning. <br>"
    "<a href='https://www.macmillancentreforlearning.co.uk/home-2/' target='_blank' style='color: #004a99; font-weight: bold; text-decoration: none;'>"
    "Go to Macmillan Centre for Learning</a>"
    "</div>", 
    unsafe_allow_html=True
)
