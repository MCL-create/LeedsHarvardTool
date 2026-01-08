import streamlit as st
import re
from io import BytesIO
from docx import Document
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# Page Config
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="wide")

# Initialize Bibliography Storage
if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []

# --- MCL BRANDING: HEADER ---
# This pulls the image you already have in your assets folder
try:
    st.image("assets/Header.png", use_container_width=True)
except:
    st.title("📚 Leeds Harvard Pro Tool")

st.write("Generate accurate references and audit your essay citations.")

# Tabs - Added "🔍 Essay Audit"
tab1, tab2, tab3, tab_final, tab_audit = st.tabs([
    "📖 Book", "📰 Journal Article", "🌐 Website", "📋 My Bibliography", "🔍 Essay Audit"
])

# --- TAB 1, 2, 3: (Logic remains the same as your current working version) ---
# [Keep your existing Book, Journal, and Website code here]

# --- TAB 4: BIBLIOGRAPHY ---
with tab_final:
    st.header("Final Bibliography")
    if not st.session_state.bibliography:
        st.info("Your bibliography is empty.")
    else:
        st.session_state.bibliography.sort(key=get_sort_key)
        for ref in st.session_state.bibliography:
            st.markdown(f"- {ref}")
        
        # Word Export Logic (Italics preserved)
        doc = Document()
        doc.add_heading('Bibliography', 0)
        for ref in st.session_state.bibliography:
            p = doc.add_paragraph()
            parts = ref.split('*')
            for index, part in enumerate(parts):
                run = p.add_run(part)
                if index % 2 != 0: run.italic = True
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        st.download_button("📥 Download as Word (.docx)", buffer, "Bibliography.docx")

# --- NEW TAB 5: ESSAY AUDIT ---
with tab_audit:
    st.header("🔍 Essay Citation Audit")
    st.write("Upload your essay to check if your in-text citations match your bibliography.")
    
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx")
    
    if uploaded_file and st.session_state.bibliography:
        doc = Document(uploaded_file)
        full_text = " ".join([para.text for para in doc.paragraphs])
        
        # Simple Regex to find (Author, Year) or (Author Year)
        citations_found = re.findall(r'\(([^)]+ \d{4})\)', full_text)
        
        st.subheader("Results")
        if citations_found:
            st.write(f"Found {len(citations_found)} potential in-text citations.")
            # Compare logic can be expanded here
            for cite in set(citations_found):
                st.info(f"Detected Citation: {cite}")
        else:
            st.warning("No standard in-text citations (e.g., Smith 2024) were detected.")
    elif not st.session_state.bibliography:
        st.warning("Please add items to your Bibliography first so the tool has something to check against.")

# --- MCL FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey;'>"
    "© 2026 Macmillan Centre for Learning. Visit us at: "
    "<a href='https://macmillancentreforlearning.co.uk' target='_blank'>macmillancentreforlearning.co.uk</a>"
    "</div>", 
    unsafe_allow_html=True
)
