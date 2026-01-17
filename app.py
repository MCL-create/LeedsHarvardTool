import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
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

# --- TAB 1: FULL GUIDE (Restored from image_d6812b.png) ---
with tabs[0]:
    st.title("Leeds Harvard Referencing Guide")
    st.markdown("""
    <div class="content-box">
    <h3>Instructions</h3>
    <p>The Leeds Harvard system is an <strong>Author-Date</strong> method. The year follows the author and is <strong>not</strong> enclosed in brackets in the bibliography.</p>
    <h4>Quick Start:</h4>
    <ol>
        <li>Add sources in the <strong>Book, Journal,</strong> or <strong>Website</strong> tabs.</li>
        <li>Review your list in the <strong>Bibliography</strong> tab and use 'One-Click Correction' for Gold Standard sources.</li>
        <li>Upload your essay in <strong>Smart Audit</strong> to check for missing citations.</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)
    
    doc_g = Document()
    doc_g.add_heading('MCL Reference Guide', 0)
    doc_g.add_paragraph('Core Formatting: Family, I. Year. Title. Place: Publisher.')
    buf_g = BytesIO(); doc_g.save(buf_g)
    st.download_button("🖨️ Download Printable Guide (.docx)", buf_g.getvalue(), "MCL_Reference_Guide.docx")

# --- TAB 6: SMART AUDIT (Restored from image_3dcbaa.png) ---
with tabs[5]:
    st.header("🔍 Smart Essay Audit")
    up = st.file_uploader("Upload Essay (.docx)", type="docx")
    if up:
        # Use the specific extractor from lht
        text = lht.extract_text_from_docx(up)
        clean_bib = [lht.clean_text(b) for b in st.session_state.bibliography]
        paragraphs = text.split('\n\n')
        results = []
        for i, p in enumerate(paragraphs):
            cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', p)
            for c in cites:
                clean_cite = lht.clean_text(c)
                matched = any(clean_cite in cb or cb in clean_cite for cb in clean_bib if cb)
                status = "✅" if matched else "❌"
                feedback = "Verified" if matched else "⚠️ Missing from Bibliography"
                # Quote Detection
                if '"' in p and not any(x in c.lower() for x in ["p.", "page"]):
                    feedback = "⚠️ Quote: Missing page number (p. X)"; status = "❌"
                results.append({"Para": i+1, "Citation": f"({c})", "Status": status, "Feedback": feedback})
        if results:
            st.table(results)

# --- TAB 7: FULL GLOSSARY (Restored from image_d60fce.png) ---
with tabs[6]:
    st.header("Glossary of Key Academic Writing Terms")
    st.markdown("""
    <div class="content-box">
        <div class="glossary-term">Plagiarism</div>
        <p><strong>Definition:</strong> Plagiarism is the act of presenting another person’s ideas, words, data, or creative work as one’s own without appropriate acknowledgement. It may be intentional or unintentional and includes copying text verbatim, closely imitating sentence structure, or submitting work produced by others, including artificial intelligence tools, without declaration (QAA, 2019).</p>
        <p>In the Scottish academic and professional learning context, plagiarism is consistent with the <strong>SSSC Codes of Practice (2024)</strong>, which emphasise honesty, integrity and responsibility in professional conduct.</p>
        <div class="example-box">
            <strong>Original source:</strong> “Assessment feedback plays a critical role...” (Nicol and Macfarlane‐Dick, 2006).<br>
            <strong>Plagiarised version:</strong> Assessment feedback plays a critical role in supporting learner development and academic confidence.<br>
            <em>Verdict: This is plagiarism because it is copied exactly with no quotation marks or citation.</em>
        </div>

        <div class="glossary-term">Paraphrasing</div>
        <p><strong>Definition:</strong> Paraphrasing involves restating another author’s ideas in one’s own words while accurately preserving the original meaning and providing an appropriate reference (Pears and Shields, 2022).</p>
        <div class="example-box">
            <strong>Correct Paraphrase:</strong> Effective feedback supports learners to reflect on their progress, engage in discussion and develop the ability to improve their own performance over time (Nicol and Macfarlane‐Dick, 2006).
        </div>

        <div class="glossary-term">Direct Quote</div>
        <p><strong>Definition:</strong> A direct quote uses the exact words of an author, enclosed within quotation marks, and must always include a citation with page number (Cottrell, 2019).</p>
        <div class="example-box">
            “Nicol and Macfarlane-Dick (2006, p. 205) argue that ‘feedback is a powerful influence’.”
        </div>
    </div>
    """, unsafe_allow_html=True)
