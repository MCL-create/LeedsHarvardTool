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

# UI STYLING
st.markdown("""
    <style>
    .stApp { background-color: #e6f7f8; } 
    div.stButton > button { background-color: #009688; color: white; border-radius: 5px; font-weight: bold; width: 100%; }
    .stTabs [aria-selected="true"] { background-color: #009688 !important; color: white !important; }
    .content-box { background-color: white; padding: 25px; border-radius: 10px; border-left: 5px solid #009688; margin-bottom: 20px; }
    .glossary-term { color: #009688; font-weight: bold; font-size: 1.4em; margin-top: 25px; border-bottom: 1px solid #eee; }
    .example-box { background-color: #f1f8f7; padding: 15px; border-radius: 5px; border: 1px dashed #009688; margin-top: 10px; font-style: normal; }
    </style>
""", unsafe_allow_html=True)

if os.path.exists("assets/Header.png"): 
    st.image("assets/Header.png", use_column_width=True)

tabs = st.tabs(["🏠 Guide", "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit", "📚 Glossary"])

# --- TAB 1: FULL GUIDE ---
with tabs[0]:
    st.title("🎓 Leeds Harvard Referencing Guide")
    st.markdown("""
    <div class="content-box">
    <h3>What is the Leeds Harvard Method?</h3>
    <p>This is an <strong>Author-Date</strong> system. It requires an in-text citation in your essay and a full bibliography at the end.</p>
    <p><strong>Correct Format:</strong> Family name, INITIAL(S). Year. Title. Edition. Place: Publisher.</p>
    <hr>
    <h4>How to Use:</h4>
    <ol>
        <li>Add sources in the <strong>Book, Journal,</strong> or <strong>Website</strong> tabs.</li>
        <li>Review and export in the <strong>Bibliography</strong> tab.</li>
        <li>Upload your essay in the <strong>Smart Audit</strong> tab to verify citations.</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Reference Examples")
    st.code("Adams, A. D. 1906. Electric transmission of water power. New York: McGraw.")
    st.code("Bowlby, J. 1998. Separation: Attachment and loss series, Vol 3. 2nd ed. London: Routledge.")

    # Printable Guide Button
    doc_g = Document()
    doc_g.add_heading('MCL Leeds Harvard Reference Guide', 0)
    doc_g.add_paragraph('Core Format: Family, I. Year. Title. Place: Publisher.')
    buf_g = BytesIO(); doc_g.save(buf_g)
    st.download_button("🖨️ Download Printable Guide (.docx)", buf_g.getvalue(), "MCL_Reference_Guide.docx")

# --- DATA INPUT TABS ---
with tabs[1]:
    st.header("Add a Book")
    with st.form("b_form"):
        ba = st.text_input("Author"); by = st.text_input("Year"); bt = st.text_input("Title"); bp = st.text_input("Publisher")
        if st.form_submit_button("Add Book"):
            st.session_state.bibliography.append(lht.generate_book_reference(ba, by, bt, bp))
            st.success("Added.")

# --- TAB 6: SMART AUDIT ---
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
        if results: st.table(results)

# --- TAB 7: FULL GLOSSARY (REPLACED WITH YOUR EXACT TEXT) ---
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
            <em>Paraphrased version (correct):</em> Effective feedback supports learners to reflect on their progress, engage in discussion and develop the ability to improve their own performance over time (Nicol and Macfarlane‐Dick, 2006).<br>
            <strong>Verdict:</strong> The meaning is retained, the wording is original, and the source is acknowledged.
        </div>

        <div class="glossary-term">Direct Quote</div>
        <p><strong>Definition:</strong> A direct quote uses the exact words of an author, enclosed within quotation marks, and must always include a citation with page number where available. Direct quotations should be used sparingly and purposefully, for example when an author’s wording is particularly authoritative or precise (Cottrell, 2019).</p>
        <p>In academic and professional writing, overuse of direct quotation can limit critical analysis; therefore, balance with paraphrasing is encouraged.</p>
        <div class="example-box">
            <strong>Example:</strong><br>
            “Nicol and Macfarlane‐Dick (2006, p. 205) argue that ‘feedback is a powerful influence on student learning and achievement’.”<br>
            <strong>Verdict:</strong> This is correct practice because the quotation marks, author, year and page number are all clearly provided.
        </div>
    </div>
    """, unsafe_allow_html=True)
