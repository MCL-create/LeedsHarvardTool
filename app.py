import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from docx.shared import Pt, Inches
import leeds_harvard_tool as lht

# --- INITIALIZATION ---
if 'bibliography' not in st.session_state: 
    st.session_state.bibliography = []

st.set_page_config(page_title="MCL Referencing Assistant", page_icon="🎓", layout="wide")

# UI STYLING
st.markdown("""
    <style>
    .stApp { background-color: #e6f7f8; } 
    div.stButton > button { background-color: #009688; color: white; border-radius: 5px; font-weight: bold; width: 100%; }
    .stTabs [aria-selected="true"] { background-color: #009688 !important; color: white !important; }
    .content-box { background-color: white; padding: 25px; border-radius: 10px; border-left: 5px solid #009688; margin-bottom: 20px; }
    .glossary-term { color: #009688; font-weight: bold; font-size: 1.3em; margin-top: 20px; border-bottom: 1px solid #eee; }
    .example-box { background-color: #f1f8f7; padding: 15px; border-radius: 5px; border: 1px dashed #009688; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

if os.path.exists("assets/Header.png"): 
    st.image("assets/Header.png", use_column_width=True)

tabs = st.tabs(["🏠 Guide", "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit", "📚 Glossary"])

# --- TAB 1: GUIDE + PRINTABLE DOWNLOAD ---
with tabs[0]:
    st.title("🎓 Leeds Harvard Referencing Guide")
    st.markdown("""
    <div class="content-box">
    <h3>Instructions & Desktop Reference</h3>
    <p>Year follows the author name and is <strong>NOT</strong> in brackets.</p>
    <p>Use the button below to download a printable desk reference containing all MCL formatting rules and the Glossary.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Logic for Printable Guide .docx
    doc_g = Document()
    doc_g.add_heading('MCL Leeds Harvard Reference Guide', 0)
    doc_g.add_heading('Core Rules', level=1)
    doc_g.add_paragraph('Books: Family, I. Year. Title. Place: Publisher.')
    doc_g.add_paragraph('Journals: Family, I. Year. Article. Journal. Vol (Iss), pp.X-Y.')
    doc_g.add_heading('Scottish Standards', level=1)
    doc_g.add_paragraph('SSSC Codes: Scottish Social Services Council. 2024. SSSC Codes of Practice...')
    buf_g = BytesIO(); doc_g.save(buf_g)
    st.download_button("🖨️ Download Printable Guide (.docx)", buf_g.getvalue(), "MCL_Reference_Guide.docx")

# --- INPUT TABS (BOOK, JOURNAL, WEBSITE) ---
with tabs[1]:
    st.header("Add a Book")
    with st.form("b_form"):
        ba = st.text_input("Author"); by = st.text_input("Year"); bt = st.text_input("Title"); bp = st.text_input("Publisher")
        if st.form_submit_button("Add Book"):
            st.session_state.bibliography.append(lht.generate_book_reference(ba, by, bt, bp))
            st.success("Added.")

with tabs[2]:
    st.header("Add a Journal")
    with st.form("j_form"):
        ja = st.text_input("Author"); jy = st.text_input("Year"); jt = st.text_input("Article"); jj = st.text_input("Journal"); jv = st.text_input("Vol"); ji = st.text_input("Issue"); jp = st.text_input("Pages")
        if st.form_submit_button("Add Journal"):
            st.session_state.bibliography.append(lht.generate_journal_reference(ja, jy, jt, jj, jv, ji, jp))
            st.success("Added.")

with tabs[3]:
    st.header("Add a Website")
    with st.form("w_form"):
        wa = st.text_input("Author/Org"); wy = st.text_input("Year"); wt = st.text_input("Title"); wu = st.text_input("URL"); wd = st.text_input("Accessed")
        if st.form_submit_button("Add Website"):
            st.session_state.bibliography.append(lht.generate_web_reference(wa, wy, wt, wu, wd))
            st.success("Added.")

# --- TAB 5: BIBLIOGRAPHY ---
with tabs[4]:
    st.header("Final Bibliography")
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

# --- TAB 6: SMART AUDIT ---
with tabs[5]:
    st.header("🔍 Smart Essay Audit")
    up = st.file_uploader("Upload Essay", type="docx")
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

# --- TAB 7: GLOSSARY ---
with tabs[6]:
    st.header("Glossary of Key Academic Writing Terms")
    st.markdown("""
    <div class="content-box">
        <div class="glossary-term">Plagiarism</div>
        <p><strong>Definition:</strong> Plagiarism is the act of presenting another person’s ideas, words, data, or creative work as one’s own without acknowledgement (QAA, 2019).</p>
        <p>This is consistent with the <strong>SSSC Codes of Practice (2024)</strong>, emphasizing honesty and integrity.</p>
        <div class="glossary-term">Paraphrasing</div>
        <p>Restating an author’s ideas in your own words while providing a reference (Pears and Shields, 2022).</p>
        <div class="glossary-term">Direct Quote</div>
        <p>Using exact words with quotation marks and a page number citation (Cottrell, 2019).</p>
    </div>
    """, unsafe_allow_html=True)
