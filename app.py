import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# --- 1. PAGE CONFIG & MCL THEME ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="centered")

# Custom CSS for MCL Blue Theme
st.markdown("""
    <style>
    .stTabs [aria-selected="true"] { background-color: #004a99 !important; color: white !important; }
    div.stButton > button:first-child { background-color: #004a99; color: white; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []

# --- 2. FIXED HEADER LOGIC ---
# Using 'use_column_width' to fix the Render TypeError
img_path = os.path.join(os.path.dirname(__file__), "assets", "Header.png")

if os.path.exists(img_path):
    st.image(img_path, use_column_width=True)
else:
    # Fallback to try relative path directly
    try:
        st.image("assets/Header.png", use_column_width=True)
    except:
        st.title("📚 MCL Leeds Harvard Pro Tool")

# --- 3. TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 Book", "📰 Journal Article", "🌐 Website", "📋 My Bibliography", "🔍 Essay Audit"
])

# (Keep your existing Tab 1-3 logic for inputs here)

# --- TAB 4: BIBLIOGRAPHY ---
with tab4:
    st.header("Final Bibliography")
    if not st.session_state.bibliography:
        st.info("Your list is empty.")
    else:
        st.session_state.bibliography.sort(key=get_sort_key)
        for ref in st.session_state.bibliography:
            st.markdown(f"- {ref}")
        
        # Word Export
        doc = Document()
        doc.add_heading('Bibliography', 0)
        for ref in st.session_state.bibliography:
            p = doc.add_paragraph()
            parts = ref.split('*')
            for i, pt in enumerate(parts):
                run = p.add_run(pt)
                if i % 2 != 0: run.italic = True
        
        buf = BytesIO()
        doc.save(buf)
        st.download_button("📥 Download Bibliography (.docx)", buf.getvalue(), "MCL_Bibliography.docx")
        if st.button("Clear List"):
            st.session_state.bibliography = []
            st.rerun()

# --- TAB 5: ESSAY AUDIT & REPORT ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx")
    
    if uploaded_file:
        doc = Document(uploaded_file)
        full_text = " ".join([p.text for p in doc.paragraphs])
        
        # Regex tuned for Leeds Harvard: (Author, Year)
        citations_found = re.findall(r'\(([^)]{5,100}?\d{4}[^)]{0,20}?)\)', full_text)
        
        if citations_found:
            st.write(f"### Results: {len(citations_found)} Citations")
            bib_joined = " ".join(st.session_state.bibliography).lower()
            
            audit_list = []
            report_text = "MCL REFERENCE AUDIT REPORT\n" + "="*30 + "\n\n"
            
            for cite in sorted(list(set(citations_found))):
                main_name = cite.split(',')[0].split(' ')[0].lower()
                status = "✅ Matched" if main_name in bib_joined else "⚠️ Missing from List"
                audit_list.append({"Citation Found": f"({cite})", "Status": status})
                report_text += f"[{status}] ({cite})\n"
            
            st.table(audit_list)
            st.download_button("📥 Download Audit Report (.txt)", report_text, "MCL_Audit_Report.txt")

# --- MCL FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey; font-size: 0.8em;'>"
    "© 2026 Macmillan Centre for Learning. <br>"
    "<a href='https://www.macmillancentreforlearning.co.uk/home-2/' target='_blank' style='color: #004a99; font-weight: bold; text-decoration: none;'>"
    "Go to Macmillan Centre for Learning</a>"
    "</div>", 
    unsafe_allow_html=True
)
