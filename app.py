import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# --- 1. THEME & PAGE CONFIG ---
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="centered")

# Custom CSS for MCL Branding (Professional Blues)
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6; border-radius: 4px 4px 0px 0px; padding: 10px;
    }
    .stTabs [aria-selected="true"] { background-color: #004a99 !important; color: white !important; }
    div.stButton > button:first-child { background-color: #004a99; color: white; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# Initialize Bibliography Storage
if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []

# --- 2. HEADER LOGIC ---
# Using absolute pathing to ensure Render finds the asset
base_path = os.path.dirname(__file__)
img_path = os.path.join(base_path, "assets", "Header.png")

if os.path.exists(img_path):
    st.image(img_path, use_container_width=True)
else:
    # Fallback if image path is different on server
    st.image("assets/Header.png", use_container_width=True)

# --- 3. TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 Book", "📰 Journal Article", "🌐 Website", "📋 My Bibliography", "🔍 Essay Audit"
])

# (Keep your existing Tab 1-3 logic here, ensuring they are inside 'with tabX:' blocks)
# [Tab 1: Book, Tab 2: Journal, Tab 3: Website code remains unchanged]

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
        
        if st.button("🗑️ Clear List"):
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
            st.write(f"### Results: {len(citations_found)} Citations Identified")
            bib_joined = " ".join(st.session_state.bibliography).lower()
            
            audit_list = []
            report_text = "MCL REFERENCE AUDIT REPORT\n" + "="*30 + "\n\n"
            
            for cite in sorted(list(set(citations_found))):
                main_name = cite.split(',')[0].split(' ')[0].lower()
                found = main_name in bib_joined
                status = "✅ Matched" if found else "⚠️ Missing from List"
                
                audit_list.append({"Citation Found": f"({cite})", "Status": status})
                report_text += f"[{status}] ({cite})\n"
            
            st.table(audit_list)
            
            # THE OUTPUT REPORT
            st.download_button(
                label="📥 Download Audit Report (.txt)",
                data=report_text,
                file_name="MCL_Audit_Report.txt",
                mime="text/plain"
            )
        else:
            st.warning("No citations detected. Ensure they follow (Author, Year).")

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
