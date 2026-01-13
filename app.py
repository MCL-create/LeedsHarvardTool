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
st.markdown("<style>.stApp { background-color: #e6f7f8; } div.stButton > button { background-color: #009688; color: white; }</style>", unsafe_allow_html=True)

if os.path.exists("assets/Header.png"): st.image("assets/Header.png", use_column_width=True)

tabs = st.tabs(["📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit", "💡 Guide"])

# --- TAB 1: BOOK ---
with tabs[0]:
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

# --- TAB 2: JOURNAL (NOW WORKING) ---
with tabs[1]:
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

# --- TAB 3: WEBSITE (NOW WORKING) ---
with tabs[2]:
    st.header("Website Reference")
    url_in = st.text_input("Paste URL")
    if st.button("Fetch Website Details"):
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

# --- TAB 4: BIBLIOGRAPHY (ONE-CLICK + EXPORT) ---
with tabs[3]:
    st.header("Bibliography")
    if st.session_state.bibliography:
        if st.button("🪄 One-Click Correction (Gold Standard)"):
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

# --- TAB 5: AUDIT ---
with tabs[4]:
    st.header("Smart Audit")
    up = st.file_uploader("Upload .docx", type="docx")
    if up and st.button("Audit Essay"):
        doc = Document(up)
        clean_bib = [lht.clean_text(b) for b in st.session_state.bibliography]
        results = []
        for i, p in enumerate(doc.paragraphs):
            cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', p.text)
            for c in cites:
                match = any(lht.clean_text(c) in cb or cb in lht.clean_text(c) for cb in clean_bib)
                results.append({"Para": i+1, "Citation": f"({c})", "Status": "✅" if match else "⚠️"})
        st.table(results)

# --- TAB 6: GUIDE ---
with tabs[5]:
    st.header("Leeds Harvard Guide")
    st.write("**What is the Leeds Harvard Method? 

The Leeds Harvard referencing style is a widely used academic system for acknowledging sources. It is based on the author–date principle: 

In-text citations: A brief reference appears within the text (author’s surname, year, and page number if quoting). 

Reference list: A full citation is provided at the end of the work, giving all the details needed to locate the source. 

This method is used to: 

Avoid plagiarism. 

Show evidence of reading and research. 

Help the reader track down sources. 

The University of Leeds has its own version of Harvard, which is slightly stricter than some other institutions (for example, in how spacing, punctuation, and access dates are presented). 

Key Features 

In-text citation 

Format: (Author, Year) or (Author, Year, p. X) if page numbers are needed. 

Example (paraphrase): 

Social workers require strong advocacy skills to empower service users (Bateman, 2000). 

Example (direct quote): 

“The casework relationship is central to effective practice” (Biestek, 1961, p. 45). 

Reference list 

Placed at the end of your work. 

Listed alphabetically by author’s surname. 

Each reference must include consistent information: author(s), year, title (in italics), edition if not the first, place of publication, and publisher. 

Online sources must include a full URL and Accessed date. 
    st.write("**In-text:** (Author, Year). **Quote:** (Author, Year, p. X).")
    st.write("**Bibliography:** Author (Year) Title. Place: Publisher.")
