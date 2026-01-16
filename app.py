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
    .guide-box { background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid #009688; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

if os.path.exists("assets/Header.png"): 
    st.image("assets/Header.png", use_column_width=True)

tabs = st.tabs(["🏠 Guide", "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit", "📚 Glossary"])

# --- TAB 1: GUIDE (WITH FULL EXAMPLES) ---
with tabs[0]:
    st.title("🎓 Leeds Harvard Referencing Guide")
    st.markdown("""
    <div class="guide-box">
    <h3>The Leeds Harvard (Author-Date) Method</h3>
    <p>Year follows the author name and is NOT in brackets in the bibliography list.</p>
    <hr>
    <h4>Step-by-Step Instructions:</h4>
    <ol>
        <li><strong>Research:</strong> Use the Book, Journal, or Website tabs to find and add your sources.</li>
        <li><strong>Finalize:</strong> Go to the Bibliography tab to sort your list and apply 'One-Click Corrections' for Scottish legislation.</li>
        <li><strong>Audit:</strong> Upload your .docx essay to the Smart Audit to check your in-text citations.</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📖 Book Examples")
        st.code("Adams, A.D. 1906. Electric transmission of water power. New York: McGraw.")
        st.code("Finch, E. and Fafinski, S. 2015. Legal skills. 5th ed. Oxford: Oxford University Press.")
        
        st.subheader("📰 Journal Examples")
        st.code("Pajunen, K. 2006. Stakeholder influences in organizational survival. Journal of Management Studies. 43 (6), pp.1261-1288.")
    
    with col2:
        st.subheader("🌐 Website Examples")
        st.code("NHS. 2023. Social care and support guide. [Online]. [Accessed 16 Jan 2026]. Available from: https://www.nhs.uk")
        
        st.subheader("⚖️ Legislation Examples")
        st.code("Great Britain. 2010. Equality Act 2010. London: The Stationery Office.")

# --- TAB 2: BOOK ---
with tabs[1]:
    st.header("Add a Book")
    b_query = st.text_input("Search Book Title")
    if b_query:
        b_matches = lht.search_books(b_query)
        if b_matches:
            b_choice = st.selectbox("Select result:", [m['label'] for m in b_matches])
            if st.button("Auto-Fill"):
                sel = next(m for m in b_matches if m['label'] == b_choice)
                st.session_state.b_auth, st.session_state.b_yr = sel['authors'], sel['year']
                st.session_state.b_tit, st.session_state.b_pub = sel['title'], sel['publisher']
    with st.form("book_form"):
        ba = st.text_input("Author(s)", value=st.session_state.get('b_auth', ''))
        by = st.text_input("Year", value=st.session_state.get('b_yr', ''))
        bt = st.text_input("Title", value=st.session_state.get('b_tit', ''))
        bp = st.text_input("Place & Publisher", value=st.session_state.get('b_pub', ''))
        if st.form_submit_button("Add to Bibliography"):
            st.session_state.bibliography.append(lht.generate_book_reference(ba, by, bt, bp))
            st.success("Book Added!")

# --- TAB 3: JOURNAL (RESTORED) ---
with tabs[2]:
    st.header("Add a Journal Article")
    with st.form("journal_form"):
        ja = st.text_input("Author(s)")
        jy = st.text_input("Year")
        jt = st.text_input("Article Title")
        jj = st.text_input("Journal Name")
        jv = st.text_input("Volume")
        ji = st.text_input("Issue")
        jp = st.text_input("Pages (e.g. 120-135)")
        if st.form_submit_button("Add Journal to Bibliography"):
            st.session_state.bibliography.append(lht.generate_journal_reference(ja, jy, jt, jj, jv, ji, jp))
            st.success("Journal Added!")

# --- TAB 4: WEBSITE ---
with tabs[3]:
    st.header("Add a Website")
    w_url = st.text_input("Paste URL")
    if st.button("Fetch Page Data"):
        w_data = lht.scrape_website(w_url)
        st.session_state.w_tit, st.session_state.w_yr = w_data['title'], w_data['year']
    with st.form("web_form"):
        wa = st.text_input("Author/Org")
        wy = st.text_input("Year", value=st.session_state.get('w_yr', ''))
        wt = st.text_input("Page Title", value=st.session_state.get('w_tit', ''))
        wd = st.text_input("Date Accessed", value="16 Jan 2026")
        if st.form_submit_button("Add Website to Bibliography"):
            st.session_state.bibliography.append(lht.generate_web_reference(wa, wy, wt, w_url, wd))
            st.success("Website Added!")

# --- TAB 5: BIBLIOGRAPHY ---
with tabs[4]:
    st.header("Final Bibliography")
    if st.session_state.bibliography:
        if st.button("🪄 One-Click Correction"):
            st.session_state.bibliography = lht.apply_one_click_corrections(st.session_state.bibliography)
            st.rerun()
        
        st.session_state.bibliography.sort()
        for r in st.session_state.bibliography: st.info(r)
        
        # Word Export
        doc = Document()
        doc.add_heading('Bibliography', 0)
        for r in st.session_state.bibliography:
            doc.add_paragraph(r).style.font.size = Pt(11)
        buf = BytesIO(); doc.save(buf)
        st.download_button("📥 Download Bibliography (.docx)", buf.getvalue(), "MCL_Bibliography.docx")
    else:
        st.info("Your bibliography is currently empty.")

# --- TAB 6: SMART AUDIT (RESTORED & STABILIZED) ---
with tabs[5]:
    st.header("🔍 Smart Essay Audit")
    up = st.file_uploader("Upload Essay", type="docx")
    if up and st.button("Run Audit Report"):
        doc = Document(up)
        clean_bib = [lht.clean_text(b) for b in st.session_state.bibliography]
        results = []
        for i, p in enumerate(doc.paragraphs):
            cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', p.text)
            for c in cites:
                clean_cite = lht.clean_text(c)
                matched = any(clean_cite in cb or cb in clean_cite for cb in clean_bib if cb)
                feedback = "Verified" if matched else "⚠️ Missing from Bibliography"
                if '"' in p.text and not any(x in c.lower() for x in ["p.", "page"]):
                    feedback = "⚠️ Quote: Missing page number (p. X)"
                    matched = False
                results.append({"Para": i+1, "Citation": f"({c})", "Status": "✅" if matched else "❌", "Feedback": feedback})
        if results:
            st.table(results)
        else:
            st.warning("No citations detected. Use (Author, Year) format.")

# --- TAB 7: GLOSSARY ---
with tabs[6]:
    st.header("📚 Glossary")
    st.markdown("""
    **Plagiarism:** Presenting someone else's ideas as your own.  
    **Paraphrasing:** Rewriting ideas in your own words (still needs a citation).  
    **Direct Quote:** Exact words (requires "marks" and page numbers).
    """)
