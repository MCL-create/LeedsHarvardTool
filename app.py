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

st.set_page_config(page_title="MCL Referencing Assistant", page_icon="🎓", layout="wide")

# UI STYLING (Preserved from image_3e400c.png)
st.markdown("""
    <style>
    .stApp { background-color: #e6f7f8; } 
    div.stButton > button { background-color: #009688; color: white; border-radius: 5px; font-weight: bold; }
    .stTabs [aria-selected="true"] { background-color: #009688 !important; color: white !important; }
    .content-box { background-color: white; padding: 25px; border-radius: 10px; border-left: 5px solid #009688; margin-bottom: 20px; }
    .glossary-term { color: #009688; font-weight: bold; font-size: 1.3em; margin-top: 15px; }
    .example-box { background-color: #f1f8f7; padding: 15px; border-radius: 5px; border: 1px dashed #009688; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

if os.path.exists("assets/Header.png"): 
    st.image("assets/Header.png", use_column_width=True)

tabs = st.tabs(["🏠 Guide", "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit", "📚 Glossary"])

# --- TAB 1: GUIDE (Includes Printable Guide Download) ---
with tabs[0]:
    st.title("Leeds Harvard Referencing Guide")
    st.markdown("""
    <div class="content-box">
    <h3>Instructions</h3>
    <p>The Leeds Harvard system follows the <strong>Author-Date</strong> format. In the bibliography, the year is never placed in brackets.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Printable Guide Logic
    doc_g = Document()
    doc_g.add_heading('MCL Reference Guide', 0)
    doc_g.add_paragraph('Follow SSSC 2024 Codes of Practice for professional writing.')
    buf_g = BytesIO(); doc_g.save(buf_g)
    st.download_button("🖨️ Download Printable Desk Reference (.docx)", buf_g.getvalue(), "MCL_Reference_Guide.docx")

# --- DATA INPUT TABS (BOOK, JOURNAL, WEBSITE) ---
# (Standard forms preserved as per previous successful builds)
with tabs[1]:
    st.header("Add a Book")
    with st.form("b_form"):
        ba = st.text_input("Author"); by = st.text_input("Year"); bt = st.text_input("Title"); bp = st.text_input("Publisher")
        if st.form_submit_button("Add Book"):
            st.session_state.bibliography.append(lht.generate_book_reference(ba, by, bt, bp))
            st.success("Added.")

# --- TAB 6: SMART AUDIT (Preserved from image_3dcbaa.png) ---
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
                results.append({"Para": i+1, "Citation": f"({c})", "Status": "✅" if matched else "❌"})
        if results:
            st.table(results)

# --- TAB 7: GLOSSARY (New Detailed Content - image_d60fce.png) ---
with tabs[6]:
    st.header("Glossary of Key Academic Writing Terms")
    st.markdown("""
    <div class="content-box">
        <div class="glossary-term">Plagiarism</div>
        <p><strong>Definition:</strong> Plagiarism is the act of presenting another person’s ideas, words, data, or creative work as one’s own without appropriate acknowledgement (QAA, 2019).</p>
        <p>In Scotland, this is consistent with the <strong>SSSC Codes of Practice (2024)</strong>, emphasizing honesty and integrity.</p>
        <div class="example-box">
            <strong>Original source:</strong> “Assessment feedback plays a critical role...” (Nicol and Macfarlane‐Dick, 2006).<br>
            <strong>Plagiarised:</strong> Assessment feedback plays a critical role...<br>
            <em>Verdict: Plagiarism (no quotes or citation).</em>
        </div>

        <div class="glossary-term">Paraphrasing</div>
        <p>Restating an author's ideas in your own words while providing a reference (Pears and Shields, 2022).</p>
        
        <div class="glossary-term">Direct Quote</div>
        <p>Uses exact words, quotation marks, and includes a page number (Cottrell, 2019).</p>
    </div>
    """, unsafe_allow_html=True)
