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
    div.stButton > button { background-color: #009688; color: white; border-radius: 5px; font-weight: bold; width: 100%; }
    .stTabs [aria-selected="true"] { background-color: #009688 !important; color: white !important; }
    .guide-box { background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #009688; }
    </style>
""", unsafe_allow_html=True)

if os.path.exists("assets/Header.png"): 
    st.image("assets/Header.png", use_column_width=True)

tabs = st.tabs(["🏠 Guide", "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit", "📚 Glossary"])

# --- TAB 1: GUIDE (THE LANDING PAGE) ---
with tabs[0]:
    st.title("🎓 Leeds Harvard Referencing Guide")
    st.markdown("""
    <div class="guide-box">
    <h3>What is the Leeds Harvard Method?</h3>
    <p>This is an <strong>Author-Date</strong> system. It requires an in-text citation in your essay and a full bibliography at the end.</p>
    <p><strong>Correct Format:</strong> Family name, INITIAL(S). Year. <em>Title</em>. Edition. Place: Publisher.</p>
    <hr>
    <h4>How to Use:</h4>
    <ol>
        <li>Add sources in the <strong>Book, Journal,</strong> or <strong>Website</strong> tabs.</li>
        <li>Review and export in the <strong>Bibliography</strong> tab.</li>
        <li>Upload your essay in the <strong>Smart Audit</strong> tab to verify your citations.</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.subheader("📚 Reference Examples")
    st.code("Adams, A.D. 1906. Electric transmission of water power. New York: McGraw.")
    st.code("Bowlby, J. 1998. Separation. Attachment and loss series, Vol 3. 2nd ed. London: Routledge.")

# --- TAB 2: BOOK (FIXED SEARCH & ADD) ---
with tabs[1]:
    st.header("Add a Book")
    b_query = st.text_input("Search by Book Title", key="book_search")
    if b_query:
        b_matches = lht.search_books(b_query)
        if b_matches:
            b_choice = st.selectbox("Select result:", [m['label'] for m in b_matches])
            if st.button("Use this Book Data"):
                sel = next(m for m in b_matches if m['label'] == b_choice)
                st.session_state.b_auth, st.session_state.b_yr = sel['authors'], sel['year']
                st.session_state.b_tit, st.session_state.b_pub = sel['title'], sel['publisher']

    with st.form("book_form"):
        col1, col2 = st.columns(2)
        with col1:
            ba = st.text_input("Author/Editor", value=st.session_state.get('b_auth', ''))
            by = st.text_input("Year", value=st.session_state.get('b_yr', ''))
            bt = st.text_input("Title", value=st.session_state.get('b_tit', ''))
        with col2:
            bp = st.text_input("Place & Publisher", value=st.session_state.get('b_pub', ''))
            bed = st.text_input("Edition (e.g. 5th ed.)")
            bser = st.text_input("Series Title (Optional)")
        
        if st.form_submit_button("Add Book to Bibliography"):
            ref = lht.generate_book_reference(ba, by, bt, bp, ed=bed, ser=bser)
            st.session_state.bibliography.append(ref)
            st.success("Book added!")

# --- TAB 4: WEBSITE (FIXED FETCH & ADD) ---
with tabs[3]:
    st.header("Add a Website")
    w_url = st.text_input("Paste Website URL")
    if st.button("Fetch Website Details"):
        w_data = lht.scrape_website(w_url)
        st.session_state.w_tit, st.session_state.w_yr = w_data['title'], w_data['year']
    
    with st.form("web_form"):
        wa = st.text_input("Author/Org")
        wy = st.text_input("Year", value=st.session_state.get('w_yr', ''))
        wt = st.text_input("Page Title", value=st.session_state.get('w_tit', ''))
        wd = st.text_input("Date Accessed (e.g. 16 Jan 2026)")
        if st.form_submit_button("Add Website to Bibliography"):
            ref = lht.generate_web_reference(wa, wy, wt, w_url, wd)
            st.session_state.bibliography.append(ref)
            st.success("Website added!")

# --- TAB 5: BIBLIOGRAPHY ---
with tabs[4]:
    st.header("Your Bibliography")
    if st.session_state.bibliography:
        if st.button("🪄 One-Click Correction"):
            st.session_state.bibliography = lht.apply_one_click_corrections(st.session_state.bibliography)
            st.rerun()
        
        st.session_state.bibliography.sort()
        for r in st.session_state.bibliography: st.info(r)
        
        doc = Document()
        doc.add_heading('Bibliography', 0)
        for r in st.session_state.bibliography:
            doc.add_paragraph(r).style.font.size = Pt(11)
        buf = BytesIO(); doc.save(buf)
        st.download_button("📥 Download (.docx)", buf.getvalue(), "MCL_Bibliography.docx")
    else:
        st.warning("List is empty.")

# --- TAB 6: SMART AUDIT ---
with tabs[5]:
    st.header("🔍 Smart Essay Audit")
    up = st.file_uploader("Upload Essay", type="docx")
    if up and st.button("Run Audit"):
        doc = Document(up)
        clean_bib = [lht.clean_text(b) for b in st.session_state.bibliography]
        results = []
        for i, p in enumerate(doc.paragraphs):
            cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', p.text)
            for c in cites:
                clean_cite = lht.clean_text(c)
                matched = any(clean_cite in cb or cb in clean_cite for cb in clean_bib if cb)
                feedback = "Verified" if matched else "⚠️ Not in Bibliography"
                if '"' in p.text and not any(x in c.lower() for x in ["p.", "page"]):
                    feedback = "⚠️ Quote: Missing page number (p. X)"
                    matched = False
                results.append({"Para": i+1, "Citation": f"({c})", "Status": "✅" if matched else "❌", "Feedback": feedback})
        st.table(results)

# --- TAB 7: GLOSSARY ---
with tabs[6]:
    st.header("📚 Academic Glossary")
    st.markdown("""
    **Plagiarism:** Presenting someone else's ideas as your own.  
    **Paraphrasing:** Rewriting ideas in your own words (citation still required).  
    **Secondary Citation:** Citing a work mentioned in another book (e.g. Smith cited in Jones).
    """)
