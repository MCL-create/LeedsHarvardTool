import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from docx.shared import Pt
import leeds_harvard_tool as lht

# --- INITIALIZATION ---
if 'bibliography' not in st.session_state: st.session_state.bibliography = []

# --- BRANDING ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="wide")
st.markdown("<style>.stApp { background-color: #e6f7f8; } div.stButton > button { background-color: #009688; color: white; border-radius: 5px; }</style>", unsafe_allow_html=True)

if os.path.exists("assets/Header.png"): st.image("assets/Header.png", use_column_width=True)

# --- REORDERED TABS ---
tabs = st.tabs(["🏠 Guide", "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit", "📚 Glossary"])

# --- TAB 1: GUIDE (OPENING PAGE) ---
with tabs[0]:
    st.title("🎓 Welcome to the Leeds Harvard Referencing Tool")
    st.markdown("""
    <div style="background-color: #009688; padding: 20px; border-radius: 10px; color: white;">
        <h3>What is the Leeds Harvard Method?</h3>
        <p>This is an <strong>Author-Date</strong> system. It ensures your academic work is credible, allows others to find your research, and protects you against plagiarism.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📝 In-text Citations")
        st.write("Required whenever you use someone else's idea.")
        st.markdown("- **Standard:** (Author, Year)\n- **Direct Quote:** (Author, Year, p. X)")
    with col_r:
        st.subheader("📚 The Bibliography")
        st.write("The alphabetical list at the end of your essay.")
        st.info("Author. (Year) Title. Edition. Place: Publisher.")
    st.divider()
    st.subheader("✅ MCL Gold Standard Reference List")
    st.info("**Bee, H. and Boyd, D. (2002)** Life Span Development. 3rd ed. London: Allyn and Bacon.")
    st.info("**SSSC (2024)** Codes of Practice for Social Service Workers and Employers.")

# --- TAB 2: BOOK ---
with tabs[1]:
    st.header("Book Reference")
    query = st.text_input("Search Book Title")
    if query:
        matches = lht.search_books(query)
        if matches:
            choice = st.selectbox("Select match:", [m['label'] for m in matches])
            if st.button("Use Book Data"):
                sel = next(m for m in matches if m['label'] == choice)
                st.session_state.b_auth, st.session_state.b_yr = sel['authors'], sel['year']
                st.session_state.b_tit, st.session_state.b_pub = sel['title'], sel['publisher']
    with st.form("book_form"):
        a = st.text_input("Author", value=st.session_state.get('b_auth', ''))
        y = st.text_input("Year", value=st.session_state.get('b_yr', ''))
        t = st.text_input("Title", value=st.session_state.get('b_tit', ''))
        p = st.text_input("Publisher", value=st.session_state.get('b_pub', ''))
        if st.form_submit_button("Add Book"):
            st.session_state.bibliography.append(lht.generate_book_reference(a,y,t,p))
            st.success("Added!")

# --- TAB 3: JOURNAL ---
with tabs[2]:
    st.header("Journal Reference")
    j_query = st.text_input("Search Article Title")
    if j_query:
        j_matches = lht.search_journals(j_query)
        if j_matches:
            j_choice = st.selectbox("Select match:", [m['label'] for m in j_matches])
            if st.button("Use Journal Data"):
                sel = next(m for m in j_matches if m['label'] == j_choice)
                st.session_state.j_auth, st.session_state.j_yr = sel['authors'], sel['year']
                st.session_state.j_tit, st.session_state.j_jou = sel['title'], sel['journal']
                st.session_state.j_v, st.session_state.j_i, st.session_state.j_p = sel['vol'], sel['iss'], sel['pgs']
    with st.form("journal_form"):
        ja = st.text_input("Author", value=st.session_state.get('j_auth', ''))
        jy = st.text_input("Year", value=st.session_state.get('j_yr', ''))
        jt = st.text_input("Article Title", value=st.session_state.get('j_tit', ''))
        jj = st.text_input("Journal", value=st.session_state.get('j_jou', ''))
        jv = st.text_input("Vol", value=st.session_state.get('j_v', ''))
        ji = st.text_input("Issue", value=st.session_state.get('j_i', ''))
        jp = st.text_input("Pages", value=st.session_state.get('j_p', ''))
        if st.form_submit_button("Add Journal"):
            st.session_state.bibliography.append(lht.generate_journal_reference(ja,jy,jt,jj,jv,ji,jp))
            st.success("Added!")

# --- TAB 4: WEBSITE ---
with tabs[3]:
    st.header("Website Reference")
    url_in = st.text_input("Paste URL")
    if st.button("Fetch Details"):
        w_data = lht.scrape_website(url_in)
        st.session_state.w_tit, st.session_state.w_yr, st.session_state.w_url = w_data['title'], w_data['year'], url_in
    with st.form("web_form"):
        wa = st.text_input("Author/Org")
        wy = st.text_input("Year", value=st.session_state.get('w_yr', ''))
        wt = st.text_input("Page Title", value=st.session_state.get('w_tit', ''))
        wu = st.text_input("URL", value=st.session_state.get('w_url', ''))
        wd = st.text_input("Accessed (e.g. 13 Jan 2026)")
        if st.form_submit_button("Add Website"):
            st.session_state.bibliography.append(lht.generate_web_reference(wa,wy,wt,wu,wd))
            st.success("Added!")

# --- TAB 5: BIBLIOGRAPHY ---
with tabs[4]:
    st.header("Bibliography Management")
    if st.session_state.bibliography:
        if st.button("🪄 One-Click Correction"):
            st.session_state.bibliography = lht.apply_one_click_corrections(st.session_state.bibliography)
            st.rerun()
        doc = Document()
        doc.add_heading('Bibliography', 0)
        st.session_state.bibliography.sort(key=lht.get_sort_key)
        for ref in st.session_state.bibliography:
            p = doc.add_paragraph(ref)
            p.style.font.name = 'Aptos'; p.style.font.size = Pt(11)
        buf = BytesIO(); doc.save(buf)
        st.download_button("📥 Download (.docx)", buf.getvalue(), "MCL_Bib.docx")
        st.divider()
        for r in st.session_state.bibliography: st.info(r)

# --- TAB 6: SMART AUDIT ---
with tabs[5]:
    st.header("🔍 Smart Audit")
    up = st.file_uploader("Upload .docx", type="docx")
    if up and st.button("Audit"):
        doc = Document(up)
        clean_bib = [lht.clean_text(b) for b in st.session_state.bibliography]
        results = []
        for i, p in enumerate(doc.paragraphs):
            cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', p.text)
            for c in cites:
                match = any(lht.clean_text(c) in cb or cb in lht.clean_text(c) for cb in clean_bib)
                results.append({"Para": i+1, "Citation": f"({c})", "Status": "✅" if match else "⚠️"})
        st.table(results)

# --- TAB 7: GLOSSARY (NEW TAB) ---
with tabs[6]:
    st.header("📚 Academic Glossary")
    st.markdown("""
    **Plagiarism:** Presenting someone else's work or ideas as your own, with or without their consent.
    
    **Paraphrasing:** Rewriting someone else's ideas in your own words. You still need an in-text citation!
    
    **Secondary Citation:** When you cite a work that is mentioned in another work (e.g., *Smith cited in Jones*).
    
    **Direct Quote:** Using the exact words from a source. Requires "quotation marks" and a page number.
    """)
