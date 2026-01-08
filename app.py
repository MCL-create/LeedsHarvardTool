import streamlit as st
import re
import os
from io import BytesIO
from docx import Document
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# Page Config
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="centered")

# Initialize Bibliography Storage
if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []

# --- MCL BRANDING: HEADER FIX ---
# We check multiple possible paths for the image to ensure Render finds it
img_path = "assets/Header.png"
if not os.path.exists(img_path):
    img_path = "Header.png" # Fallback if it's in the root

if os.path.exists(img_path):
    st.image(img_path, use_container_width=True)
else:
    st.title("📚 MCL Leeds Harvard Pro Tool")

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 Book", "📰 Journal Article", "🌐 Website", "📋 My Bibliography", "🔍 Essay Audit"
])

# [Note: Keep your existing Tab 1, 2, 3, and 4 code the same as the previous version]
# ... (Previous logic for Books, Journals, and Websites goes here) ...

# --- TAB 5: ESSAY AUDIT WITH DOWNLOADABLE REPORT ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx")
    
    if uploaded_file:
        doc = Document(uploaded_file)
        full_text = " ".join([p.text for p in doc.paragraphs])
        
        # Regex to find Leeds citations (Author, Year)
        citations_found = re.findall(r'\(([^)]{5,100}?\d{4}[^)]{0,20}?)\)', full_text)
        
        if citations_found:
            st.write(f"### Found {len(citations_found)} Citations")
            bib_joined = " ".join(st.session_state.bibliography).lower()
            
            audit_list = []
            missing_report_text = "MCL ESSAY AUDIT REPORT - MISSING CITATIONS\n" + "="*40 + "\n\n"
            
            for cite in sorted(list(set(citations_found))):
                main_name = cite.split(',')[0].split(' ')[0].lower()
                is_missing = main_name not in bib_joined
                status = "⚠️ Missing from List" if is_missing else "✅ Matched"
                
                audit_list.append({"Citation Found": f"({cite})", "Status": status})
                
                if is_missing:
                    missing_report_text += f"- ({cite})\n"
            
            st.table(audit_list)
            
            # THE OUTPUT REPORT BUTTON
            st.download_button(
                label="📥 Download Missing Citations Report",
                data=missing_report_text,
                file_name="MCL_Missing_Citations.txt",
                mime="text/plain"
            )
        else:
            st.warning("No citations detected. Ensure they follow (Author, Year).")

# --- MCL FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey; font-size: 0.8em;'>"
    "© 2026 Macmillan Centre for Learning. <br>"
    "<a href='https://www.macmillancentreforlearning.co.uk/home-2/' target='_blank' style='color: #007bff; text-decoration: none;'>"
    "Go to Macmillan Centre for Learning</a>"
    "</div>", 
    unsafe_allow_html=True
)
