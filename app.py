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
    .glossary-term { color: #009688; font-weight: bold; font-size: 1.4em; margin-top: 25px; border-bottom: 1px solid #eee; }
    .example-box { background-color: #f1f8f7; padding: 15px; border-radius: 5px; border: 1px dashed #009688; margin-top: 10px; }
    .citation-ex { font-family: monospace; background-color: #f9f9f9; padding: 5px; border-radius: 3px; display: block; margin-bottom: 5px; border: 1px solid #ddd; }
    </style>
""", unsafe_allow_html=True)

if os.path.exists("assets/Header.png"): 
    st.image("assets/Header.png", use_column_width=True)

tabs = st.tabs(["🏠 Guide", "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit", "📚 Glossary"])

# --- TAB 1: GUIDE (Restored instructions & examples) ---
with tabs[0]:
    st.title("🎓 Leeds Harvard Referencing Guide")
    st.markdown("""
    <div class="content-box">
    <h3>Quick Start:</h3>
    <ol>
        <li>Add sources in the <strong>Book, Journal,</strong> or <strong>Website</strong> tabs.</li>
        <li>Review your list in the <strong>Bibliography</strong> tab and use 'One-Click Correction'.</li>
        <li>Upload your essay in <strong>Smart Audit</strong> to check for missing citations.</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Reference Examples")
    st.markdown("""
    <div class="content-box">
    <strong>Book example:</strong> <em>Smith, J. (2022) Understanding professional practice. 2nd edn. London: Routledge.</em><br>
    <strong>Journal example:</strong> <em>Brown, L. and Green, T. (2023) ‘Developing reflective capacity’, Journal of Education, 36(4), pp. 415–431.</em>
    </div>
    """, unsafe_allow_html=True)

    doc_g = Document(); doc_g.add_heading('MCL Reference Guide', 0)
    buf_g = BytesIO(); doc_g.save(buf_g)
    st.download_button("🖨️ Download Printable Guide (.docx)", buf_g.getvalue(), "MCL_Reference_Guide.docx")

# --- DATA INPUT TABS (Functioning with Italics) ---
with tabs[1]:
    st.header("Add a Book")
    with st.form("b_form"):
        ba = st.text_input("Author"); by = st.text_input("Year"); bt = st.text_input("Title"); bp = st.text_input("Publisher")
        if st.form_submit_button("Add Book"):
            if not ba or not by: st.warning("Please provide Author and Year.")
            else:
                st.session_state.bibliography.append(lht.generate_book_reference(ba, by, bt, bp))
                st.success("Added with italics.")

# --- TAB 5: BIBLIOGRAPHY (Alpha-sort & Italicized Export) ---
with tabs[4]:
    st.header("📋 Your Bibliography")
    if st.session_state.bibliography:
        if st.button("🪄 One-Click Correction (Scottish Standards)"):
            st.session_state.bibliography = lht.apply_one_click_corrections(st.session_state.bibliography)
            st.rerun()
        st.session_state.bibliography.sort()
        for r in st.session_state.bibliography:
            st.markdown(f"- {r}", unsafe_allow_html=True)
        
        doc_b = Document(); doc_b.add_heading('Bibliography', 0)
        for r in st.session_state.bibliography:
            p = doc_b.add_paragraph()
            parts = re.split(r'(<i>.*?</i>)', r)
            for part in parts:
                if part.startswith('<i>'):
                    p.add_run(part.replace('<i>','').replace('</i>','')).italic = True
                else:
                    p.add_run(part)
        buf_b = BytesIO(); doc_b.save(buf_b)
        st.download_button("📥 Download Bibliography (.docx)", buf_b.getvalue(), "MCL_Bibliography.docx")

# --- TAB 6: SMART AUDIT (Review & Identification) ---
with tabs[5]:
    st.header("🔍 Smart Essay Audit")
    up = st.file_uploader("Upload Essay (.docx)", type="docx")
    if up:
        text = lht.extract_text_from_docx(up)
        clean_bib = [lht.clean_text(b) for b in st.session_state.bibliography]
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        results = []
        for i, p in enumerate(paragraphs):
            cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', p)
            for c in cites:
                clean_cite = lht.clean_text(c)
                matched = any(clean_cite in cb for cb in clean_bib if cb)
                status = "✅" if matched else "❌"
                feedback = "Verified" if matched else "⚠️ Missing from Bibliography"
                if '"' in p and not any(x in c.lower() for x in ["p.", "page"]):
                    feedback = "⚠️ Quote: Missing page number (p. X)"; status = "❌"
                results.append({"Para": i+1, "Citation": f"({c})", "Status": status, "Feedback": feedback})
        if results:
            st.table(results)
            doc_r = Document(); doc_r.add_heading('Audit Narrative Report', 0)
            for res in results: doc_r.add_paragraph(f"Para {res['Para']}: {res['Citation']} - {res['Feedback']}")
            buf_r = BytesIO(); doc_r.save(buf_r)
            st.download_button("📊 Download Audit Report (.docx)", buf_r.getvalue(), "Audit_Narrative_Report.docx")

# --- TAB 7: GLOSSARY (Full Restored SSSC/QAA Text) ---
with tabs[6]:
    st.header("Glossary of Key Academic Writing Terms")
    st.markdown("""
    <div class="content-box">
        <div class="glossary-term">Plagiarism</div>
        <p><strong>Definition:</strong> Plagiarism is the act of presenting another person’s ideas, words, data, or creative work as one’s own without appropriate acknowledgement (QAA, 2019).</p>
        <p>In the Scottish academic and professional learning context, plagiarism is consistent with the <strong>SSSC Codes of Practice (2024)</strong>, which emphasise honesty, integrity and responsibility in professional conduct.</p>
        <div class="example-box">
            <strong>Original:</strong> “Assessment feedback plays a critical role...” (Nicol and Macfarlane-Dick, 2006).<br>
            <strong>Verdict:</strong> Plagiarism if copied exactly with no quotation marks or citation.
        </div>
        <div class="glossary-term">Direct Quote</div>
        <p><strong>Definition:</strong> A direct quote uses exact words, enclosed in quotation marks, and must include a page number (Cottrell, 2019).</p>
    </div>
    """, unsafe_allow_html=True)
