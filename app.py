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

# --- UI STYLING ---
st.markdown("""
    <style>
    .stApp { background-color: #e6f7f8; } 
    div.stButton > button { background-color: #009688; color: white; border-radius: 5px; font-weight: bold; }
    .stTabs [aria-selected="true"] { background-color: #009688 !important; color: white !important; }
    .content-box { background-color: white; padding: 25px; border-radius: 10px; border-left: 5px solid #009688; margin-bottom: 20px; }
    .glossary-term { color: #009688; font-weight: bold; font-size: 1.25em; margin-top: 20px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    .example-box { background-color: #f9fdfd; padding: 15px; border-radius: 5px; border: 1px solid #d1ecea; margin-top: 10px; font-size: 0.95em; }
    </style>
""", unsafe_allow_html=True)

if os.path.exists("assets/Header.png"): 
    st.image("assets/Header.png", use_column_width=True)

tabs = st.tabs(["🏠 Guide", "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit", "📚 Glossary"])

# --- TAB 1: GUIDE ---
with tabs[0]:
    st.title("🎓 Leeds Harvard Referencing Guide")
    st.markdown("""
    <div class="content-box">
    <h3>Instructions:</h3>
    <ol>
        <li>Add sources in the <strong>Book, Journal,</strong> or <strong>Website</strong> tabs.</li>
        <li>Review and export in the <strong>Bibliography</strong> tab.</li>
        <li>Upload your essay in the <strong>Smart Audit</strong> tab to verify citations.</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📖 Books & Journals")
        st.code("Adams, A.D. 1906. Electric transmission of water power. New York: McGraw.")
        st.code("Pajunen, K. 2006. Journal of Management Studies. 43 (6), pp.1261-1288.")
    with col2:
        st.subheader("🌐 Web & Legislation")
        st.code("NHS. 2023. Social care guide. [Online]. [Accessed 16 Jan 2026].")
        st.code("Great Britain. 2010. Equality Act 2010. London: The Stationery Office.")

# --- TABS 2-4: DATA INPUT (STABILIZED) ---
with tabs[1]:
    st.header("Add a Book")
    with st.form("b_form"):
        ba = st.text_input("Author"); by = st.text_input("Year"); bt = st.text_input("Title"); bp = st.text_input("Publisher")
        if st.form_submit_button("Add Book"):
            st.session_state.bibliography.append(lht.generate_book_reference(ba, by, bt, bp))
            st.success("Added to list.")

with tabs[2]:
    st.header("Add a Journal")
    with st.form("j_form"):
        ja = st.text_input("Author"); jy = st.text_input("Year"); jt = st.text_input("Article"); jj = st.text_input("Journal"); jv = st.text_input("Vol"); ji = st.text_input("Issue"); jp = st.text_input("Pages")
        if st.form_submit_button("Add Journal"):
            st.session_state.bibliography.append(lht.generate_journal_reference(ja, jy, jt, jj, jv, ji, jp))
            st.success("Added to list.")

with tabs[3]:
    st.header("Add a Website")
    with st.form("w_form"):
        wa = st.text_input("Author/Org"); wy = st.text_input("Year"); wt = st.text_input("Title"); wu = st.text_input("URL"); wd = st.text_input("Accessed")
        if st.form_submit_button("Add Website"):
            st.session_state.bibliography.append(lht.generate_web_reference(wa, wy, wt, wu, wd))
            st.success("Added to list.")

# --- TAB 5: BIBLIOGRAPHY + DOWNLOAD ---
with tabs[4]:
    st.header("Your Bibliography")
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
        st.download_button("📥 Download Bibliography (.docx)", buf_b.getvalue(), "MCL_Bibliography.docx")
    else:
        st.warning("List is empty.")

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
            st.download_button("📥 Download Audit Report (.docx)", buf_r.getvalue(), "MCL_Audit_Report.docx")

# --- TAB 7: GLOSSARY (FULL DETAILED VERSION) ---
with tabs[6]:
    st.header("Glossary of Key Academic Writing Terms")
    st.markdown("""
    <div class="content-box">
        <div class="glossary-term">Plagiarism</div>
        <p><strong>Definition:</strong> Plagiarism is the act of presenting another person’s ideas, words, data, or creative work as one’s own without appropriate acknowledgement. It may be intentional or unintentional and includes copying text verbatim, closely imitating sentence structure, or submitting work produced by others, including artificial intelligence tools, without declaration (QAA, 2019).</p>
        <p>In the Scottish academic and professional learning context, plagiarism is considered a breach of academic integrity and professional values, undermining trust, accountability and ethical practice. These principles are consistent with the <strong>SSSC Codes of Practice (2024)</strong>, which emphasise honesty, integrity and responsibility in professional conduct.</p>
        <div class="example-box">
            <strong>Example:</strong><br>
            <em>Original source:</em> “Assessment feedback plays a critical role in supporting learner development and academic confidence” (Nicol and Macfarlane‐Dick, 2006).<br>
            <em>Plagiarised version (incorrect):</em> Assessment feedback plays a critical role in supporting learner development and academic confidence.<br>
            <strong>Verdict:</strong> This is plagiarism because the sentence is copied exactly with no quotation marks or citation.
        </div>

        <div class="glossary-term">Paraphrasing</div>
        <p><strong>Definition:</strong> Paraphrasing involves restating another author’s ideas in one’s own words while accurately preserving the original meaning and providing an appropriate reference. Effective paraphrasing demonstrates understanding, critical engagement and academic skill rather than simple word substitution (Pears and Shields, 2022).</p>
        <p>In professional education and training settings, paraphrasing supports reflective and analytical writing by allowing learners to integrate theory into practice while maintaining academic integrity.</p>
        <div class="example-box">
            <strong>Example:</strong><br>
            <em>Original source:</em> “Good feedback practice encourages dialogue, supports self-regulation and helps learners close the gap between current and desired performance” (Nicol and Macfarlane‐Dick, 2006).<br>
            <em>Paraphrased version (correct):</em> Effective feedback supports learners to reflect on their progress, engage in discussion and develop the ability to improve their own performance over time (Nicol and Macfarlane‐Dick, 2006).
        </div>

        <div class="glossary-term">Direct Quote</div>
        <p><strong>Definition:</strong> A direct quote uses the exact words of an author, enclosed within quotation marks, and must always include a citation with page number where available. Direct quotations should be used sparingly and purposefully, for example when an author’s wording is particularly authoritative or precise (Cottrell, 2019).</p>
        <div class="example-box">
            <strong>Example:</strong><br>
            “Nicol and Macfarlane‐Dick (2006, p. 205) argue that ‘feedback is a powerful influence on student learning and achievement’.”<br>
            <strong>Verdict:</strong> This is correct practice because the quotation marks, author, year and page number are all clearly provided.
        </div>
    </div>
    """, unsafe_allow_html=True)
