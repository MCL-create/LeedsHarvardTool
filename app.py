import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# --- 1. MCL BRANDED THEME ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="centered")

# Custom CSS using official MCL Hex Codes
st.markdown(f"""
    <style>
    .stApp {{ background-color: #e6f7f8; color: #37474f; }}
    .stTabs [aria-selected="true"] {{ background-color: #009688 !important; color: white !important; }}
    div.stButton > button {{ background-color: #009688; color: white; border-radius: 5px; }}
    .explanation-box {{ 
        background-color: #dff7f9; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #f9a825; 
        margin-top: 10px;
    }}
    </style>
""", unsafe_allow_html=True)

if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []

# --- 2. HEADER ---
img_path = "assets/Header.png"
if os.path.exists(img_path):
    st.image(img_path, use_column_width=True)

# --- 3. TABS ---
# Adding unique keys to tabs and widgets ensures they remain active
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 Book", "📰 Journal", "🌐 Website", "📋 Bibliography", "🔍 Essay Audit"
])

# Example of a Fixed Interactive Tab
with tab1:
    st.header("Book Reference")
    with st.form("book_form_v2"):
        auth = st.text_input("Authors (comma separated)", key="book_auth")
        yr = st.text_input("Year", key="book_year")
        tit = st.text_input("Book Title", key="book_title")
        if st.form_submit_button("Add to Bibliography"):
            if auth and yr and tit:
                res = generate_book_reference([a.strip() for a in auth.split(",")], yr, tit, "", "", "")
                st.session_state.bibliography.append(res)
                st.success("Added!")

# --- TAB 5: AUDIT WITH EXPLANATIONS ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx", key="audit_uploader_v2")
    
    if uploaded_file:
        if st.button("Run Audit & Generate Report", key="audit_trigger"):
            doc = Document(uploaded_file)
            full_text = " ".join([p.text for p in doc.paragraphs])
            cites = re.findall(r'\(([^)]{5,100}?\d{4}[^)]{0,20}?)\)', full_text)
            
            if cites:
                bib_content = " ".join(st.session_state.bibliography).lower()
                audit_results = []
                missing_count = 0
                
                for c in sorted(list(set(cites))):
                    name = c.split(',')[0].split(' ')[0].lower()
                    found = name in bib_content
                    status = "✅ Matched" if found else "⚠️ Missing"
                    if not found: missing_count += 1
                    audit_results.append({"Citation": f"({c})", "Status": status})
                
                st.table(audit_results)
                
                # --- EXPLANATION SECTION ---
                if missing_count > 0:
                    st.markdown('<div class="explanation-box">', unsafe_allow_html=True)
                    st.subheader("💡 Why are some citations missing?")
                    st.write("""
                    1. **Spelling Mismatch:** Ensure the surname in your essay matches the bibliography exactly.
                    2. **Unsaved Progress:** Check if you added the reference in the 'Book' or 'Journal' tab before running the audit.
                    3. **Date Formatting:** The tool looks for 4-digit years. Ensure your citation includes the year of publication.
                    """)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.download_button("📥 Download Report (.txt)", "Report Content...", "MCL_Audit.txt", key="dl_report_v2")
