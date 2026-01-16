import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from docx.shared import Pt
import leeds_harvard_tool as lht

# --- INITIALIZATION ---
if 'bibliography' not in st.session_state: 
    st.session_state.bibliography = []

st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="wide")

# UI Styling
st.markdown("""
    <style>
    .stApp { background-color: #e6f7f8; } 
    div.stButton > button { background-color: #009688; color: white; border-radius: 5px; font-weight: bold; width: 100%; }
    .stTabs [aria-selected="true"] { background-color: #009688 !important; color: white !important; }
    .guide-box { background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #009688; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

if os.path.exists("assets/Header.png"): 
    st.image("assets/Header.png", use_column_width=True)

tabs = st.tabs(["🏠 Guide", "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit", "📚 Glossary"])

# --- TAB 1: FULL GUIDE (RESTORED) ---
with tabs[0]:
    st.title("🎓 Leeds Harvard Referencing Guide")
    st.markdown("""
    <div class="guide-box">
    <h3>The Leeds Harvard Method</h3>
    <p>This Author-Date system requires the Year to follow the author name without brackets in the bibliography.</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📖 Book & Journal Examples")
        st.code("Adams, A.D. 1906. Electric transmission of water power. New York: McGraw.")
        st.code("Pajunen, K. 2006. Stakeholder influences in organizational survival. Journal of Management Studies. 43 (6), pp.1261-1288.")
    with col2:
        st.subheader("🌐 Website & Legislation")
        st.code("NHS. 2023. Social care guide. [Online]. [Accessed 16 Jan 2026]. Available from: https://www.nhs.uk")
        st.code("Great Britain. 2010. Equality Act 2010. London: The Stationery Office.")

# --- TABS 2-4: DATA INPUT (RESTORED) ---
with tabs[1]:
    st.header("Add Book")
    with st.form("b_form"):
        ba = st.text_input("Author"); by = st.text_input("Year"); bt = st.text_input("Title"); bp = st.text_input("Publisher")
        if st.form_submit_button("Add Book"):
            st.session_state.bibliography.append(lht.generate_book_reference(ba, by, bt, bp))
            st.success("Added")

with tabs[2]:
    st.header("Add Journal")
    with st.form("j_form"):
        ja = st.text_input("Author"); jy = st.text_input("Year"); jt = st.text_input("Article"); jj = st.text_input("Journal"); jv = st.text_input("Vol"); ji = st.text_input("Issue"); jp = st.text_input("Pages")
        if st.form_submit_button("Add Journal"):
            st.session_state.bibliography.append(lht.generate_journal_reference(ja, jy, jt, jj, jv, ji, jp))
            st.success("Added")

with tabs[3]:
    st.header("Add Website")
    with st.form("w_form"):
        wa = st.text_input("Author/Org"); wy = st.text_input("Year"); wt = st.text_input("Title"); wu = st.text_input("URL"); wd = st.text_input("Accessed")
        if st.form_submit_button("Add Website"):
            st.session_state.bibliography.append(lht.generate_web_reference(wa, wy, wt, wu, wd))
            st.success("Added")

# --- TAB 5: BIBLIOGRAPHY + DOWNLOAD ---
with tabs[4]:
    st.header("Bibliography")
    if st.session_state.bibliography:
        if st.button("🪄 One-Click Correction"):
            st.session_state.bibliography = lht.apply_one_click_corrections(st.session_state.bibliography)
            st.rerun()
        st.session_state.bibliography.sort()
        for r in st.session_state.bibliography: st.info(r)
        
        doc_b = Document()
        doc_b.add_heading('Bibliography', 0)
        for r in st.session_state.bibliography: doc_b.add_paragraph(r).style.font.size = Pt(11)
        buf_b = BytesIO(); doc_b.save(buf_b)
        st.download_button("📥 Download Bibliography (.docx)", buf_b.getvalue(), "Bibliography.docx")

# --- TAB 6: SMART AUDIT + REPORT DOWNLOAD ---
with tabs[5]:
    st.header("🔍 Smart Essay Audit")
    up = st.file_uploader("Upload Essay (.docx)", type="docx")
    if up:
        doc = Document(up)
        clean_bib = [lht.clean_text(b) for b in st.session_state.bibliography]
        results = []
        for i, p in enumerate(doc.paragraphs):
            cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', p.text)
            for c in cites:
                clean_cite = lht.clean_text(c)
                matched = any(clean_cite in cb or cb in clean_cite for cb in clean_bib if cb)
                fb = "Verified" if matched else "⚠️ Missing from Bibliography"
                if '"' in p.text and not any(x in c.lower() for x in ["p.", "page"]):
                    fb = "⚠️ Quote: Missing page number (p. X)"; matched = False
                results.append({"Para": i+1, "Citation": f"({c})", "Status": "✅" if matched else "❌", "Feedback": fb})
        
        if results:
            st.table(results)
            doc_r = Document()
            doc_r.add_heading('MCL Referencing Audit Report', 0)
            table = doc_r.add_table(rows=1, cols=4); table.style = 'Table Grid'
            hdr = table.rows[0].cells
            hdr[0].text = 'Para'; hdr[1].text = 'Citation'; hdr[2].text = 'Status'; hdr[3].text = 'Feedback'
            for res in results:
                row = table.add_row().cells
                row[0].text = str(res['Para']); row[1].text = res['Citation']
                row[2].text = res['Status']; row[3].text = res['Feedback']
            buf_r = BytesIO(); doc_r.save(buf_r)
            st.download_button("📥 Download Audit Report (.docx)", buf_r.getvalue(), "Audit_Report.docx")

with tabs[6]:
    st.header("📚 Glossary")
    st.write("**Plagiarism:** Using ideas without credit. **Paraphrase:** Own words (needs cite). **Quote:** Exact words (needs p. number).")
