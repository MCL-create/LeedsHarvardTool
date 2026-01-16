import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import leeds_harvard_tool as lht

# --- INITIALIZATION ---
if 'bibliography' not in st.session_state: 
    st.session_state.bibliography = []

# --- BRANDING ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #e6f7f8; } 
    div.stButton > button { background-color: #009688; color: white; border-radius: 5px; font-weight: bold; }
    .stTabs [aria-selected="true"] { background-color: #009688 !important; color: white !important; }
    .instruction-card { background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid #009688; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

if os.path.exists("assets/Header.png"): 
    st.image("assets/Header.png", use_column_width=True)

# --- TABS ---
tabs = st.tabs(["🏠 Guide", "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit", "📚 Glossary"])

# --- TAB 1: GUIDE ---
with tabs[0]:
    st.title("🎓 Welcome to the MCL Referencing Assistant")
    st.markdown("""
    <div style="background-color: #009688; padding: 20px; border-radius: 10px; color: white;">
        <h3>How to use this tool:</h3>
        <p>1. Add your sources using the <strong>Book, Journal,</strong> or <strong>Website</strong> tabs.</p>
        <p>2. Review your list in the <strong>Bibliography</strong> tab and use 'One-Click Correction'.</p>
        <p>3. Upload your essay to the <strong>Smart Audit</strong> to check for missing citations or quote errors.</p>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📝 In-Text Citations")
        st.markdown("- **Paraphrase:** (Author, Year)\n- **Direct Quote:** (Author, Year, p. X)")
    with col2:
        st.subheader("🖨️ Printable Guide")
        st.write("Your downloaded Bibliography will include a 'Quick Reference' cover sheet for your desk.")

# --- TAB 2: BOOK ---
with tabs[1]:
    st.header("Book Reference")
    query = st.text_input("Search Book Title")
    if query:
        matches = lht.search_books(query)
        if matches:
            choice = st.selectbox("Select match:", [m['label'] for m in matches])
            if st.button("Use Data"):
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
    if st.button("Fetch"):
        w_data = lht.scrape_website(url_in)
        st.session_state.w_tit, st.session_state.w_yr, st.session_state.w_url = w_data['title'], w_data['year'], url_in
    with st.form("web_form"):
        wa = st.text_input("Author/Org")
        wy = st.text_input("Year", value=st.session_state.get('w_yr', ''))
        wt = st.text_input("Page Title", value=st.session_state.get('w_tit', ''))
        wu = st.text_input("URL", value=st.session_state.get('w_url', ''))
        wd = st.text_input("Accessed (e.g. 16 Jan 2026)")
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
        
        # Doc Generation
        doc = Document()
        doc.add_heading('Leeds Harvard Reference Guide', 0)
        doc.add_paragraph("In-text: (Author, Year) | Quote: (Author, Year, p. X)").alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_page_break()
        doc.add_heading('Bibliography', 1)
        st.session_state.bibliography.sort(key=lht.get_sort_key)
        for ref in st.session_state.bibliography:
            p = doc.add_paragraph(ref)
            p.style.font.name = 'Aptos'; p.style.font.size = Pt(11)
        
        buf = BytesIO(); doc.save(buf)
        st.download_button("📥 Download Bibliography & Guide", buf.getvalue(), "MCL_Bibliography.docx")
        st.divider()
        for r in st.session_state.bibliography: st.info(r)
    else:
        st.info("Your bibliography is empty.")

# --- TAB 6: SMART AUDIT ---
with tabs[5]:
    st.header("🔍 Smart Essay Audit")
    up = st.file_uploader("Upload .docx", type="docx")
    if up and st.button("Audit"):
        doc = Document(up)
        clean_bib = [lht.clean_text(b) for b in st.session_state.bibliography]
        results = []
        for i, p in enumerate(doc.paragraphs):
            cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', p.text)
            for c in cites:
                clean_cite = lht.clean_text(c)
                matched = any(clean_cite in cb or cb in clean_cite for cb in clean_bib if cb)
                feedback = "Reference verified." if matched else "⚠️ Missing from Bibliography."
                if '"' in p.text and not any(x in c.lower() for x in ["p.", "page"]):
                    feedback = "⚠️ Quote detected: Missing page number (p. X)."
                    matched = False
                results.append({"Para": i+1, "Citation": f"({c})", "Status": "✅" if matched else "❌", "Feedback": feedback})
        st.table(results)

# --- TAB 7: GLOSSARY ---
with tabs[6]:
    st.header("📚 Academic Glossary")
    st.markdown("""
    **Plagiarism:** Using ideas without credit.  
    **Paraphrase:** Writing in your own words.  
    **Direct Quote:** Exact words (needs "marks" and page numbers).  
    **Secondary Citation:** Citing a source mentioned in another source.
    """)
