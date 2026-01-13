import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from docx.shared import Pt
import leeds_harvard_tool as lht

# --- 1. INITIALIZATION ---
if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []

# --- 2. MCL BRANDED THEME ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #e6f7f8; color: #37474f; }
    .stTabs [aria-selected="true"] { background-color: #009688 !important; color: white !important; }
    div.stButton > button { background-color: #009688; color: white; border-radius: 5px; font-weight: bold; width: 100%; }
    .stInfo { background-color: #ffffff; border-left: 5px solid #009688; }
    </style>
""", unsafe_allow_html=True)

# --- 3. BRANDED HEADER ---
if os.path.exists("assets/Header.png"):
    st.image("assets/Header.png", use_column_width=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Smart Audit"])

# --- TAB 1: BOOK ---
with tab1:
    st.header("Book Reference")
    query = st.text_input("Magic Search (Title/Author)")
    if query:
        matches = lht.search_books(query)
        if matches:
            choice = st.selectbox("Select match:", [m['label'] for m in matches])
            if st.button("Magic Fill"):
                sel = next(m for m in matches if m['label'] == choice)
                st.session_state.k_b_auth = sel['authors']; st.session_state.k_b_yr = sel['year']
                st.session_state.k_b_tit = sel['title']; st.session_state.k_b_pub = sel['publisher']
    
    with st.form("book_form", clear_on_submit=True):
        auth = st.text_input("Authors", value=st.session_state.get('k_b_auth', ''))
        yr = st.text_input("Year", value=st.session_state.get('k_b_yr', ''))
        tit = st.text_input("Title", value=st.session_state.get('k_b_tit', ''))
        pub = st.text_input("Publisher", value=st.session_state.get('k_b_pub', ''))
        if st.form_submit_button("Add to Bibliography"):
            st.session_state.bibliography.append(lht.generate_book_reference(auth, yr, tit, pub))
            st.success("Reference added.")

# (Tabs 2 & 3 would follow the same pattern for Journals and Websites)

# --- TAB 4: BIBLIOGRAPHY ---
with tab4:
    st.header("Manage Bibliography")
    if st.session_state.bibliography:
        if st.button("🪄 Fix My Bibliography (One-Click Correction)"):
            st.session_state.bibliography = lht.apply_one_click_corrections(st.session_state.bibliography)
            st.success("Bibliography entries have been matched to the MCL Gold Standard.")
            st.rerun()

    st.divider()
    st.session_state.bibliography.sort(key=lht.get_sort_key)
    for ref in st.session_state.bibliography:
        st.info(ref)
    
    if st.button("Clear All"):
        st.session_state.bibliography = []; st.rerun()

# --- TAB 5: SMART AUDIT ---
with tab5:
    st.header("🔍 Smart Essay Audit")
    uploaded = st.file_uploader("Upload Essay (.docx)", type="docx")
    if uploaded:
        if st.button("Run Audit"):
            doc = Document(uploaded)
            clean_bib = [lht.clean_text(b) for b in st.session_state.bibliography]
            results = []
            for i, p in enumerate(doc.paragraphs):
                cites = re.findall(r'\(([^)]{2,100}?\d{4}[^)]{0,50}?)\)', p.text)
                for c in cites:
                    clean_cite = lht.clean_text(c)
                    matched = any(cb in clean_cite or clean_cite in cb for cb in clean_bib if cb)
                    feedback = "Correct." if matched else "Not found in Bibliography."
                    
                    if '"' in p.text and not any(x in c.lower() for x in ["p.", "page"]):
                        feedback = "Direct Quote: Needs page number (p. X)."
                        matched = False
                    
                    results.append({"Para": i+1, "Citation": f"({c})", "Status": "✅" if matched else "⚠️", "Feedback": feedback})
            st.table(results)
