import streamlit as st
import re
from io import BytesIO
from docx import Document
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# Page Config
st.set_page_config(page_title="MCL Leeds Harvard Tool", page_icon="📚", layout="centered")

# Initialize Bibliography Storage
if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []

# --- MCL BRANDING: HEADER ---
# Updated path to match your GitHub structure: assets/Header.png
try:
    st.image("assets/Header.png", use_container_width=True)
except Exception:
    st.title("📚 Leeds Harvard Pro Tool")

st.write("Generate accurate references and audit your essay citations.")

# --- TABS DEFINITION ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 Book", "📰 Journal Article", "🌐 Website", "📋 My Bibliography", "🔍 Essay Audit"
])

# --- TAB 1: BOOK ---
with tab1:
    st.header("Book Reference")
    with st.form("book_form"):
        authors = st.text_input("Authors (comma separated)", placeholder="e.g. Smith, J., Doe, R.")
        year = st.text_input("Year of Publication", placeholder="2024")
        title = st.text_input("Book Title")
        edition = st.text_input("Edition (leave blank if 1st)", placeholder="e.g. 2nd")
        place = st.text_input("Place of Publication", placeholder="London")
        publisher = st.text_input("Publisher", placeholder="Pearson")
        submit_book = st.form_submit_button("Generate & Add to List")

    if submit_book:
        if authors and year and title:
            auth_list = [a.strip() for a in authors.split(",")]
            result = generate_book_reference(auth_list, year, title, publisher, place, edition)
            st.session_state.bibliography.append(result)
            st.success("Reference added to your Bibliography!")
            st.markdown(f"> {result}")
        else:
            st.error("Please fill in at least Authors, Year, and Title.")

# --- TAB 2: JOURNAL ---
with tab2:
    st.header("Journal Reference")
    with st.form("journal_form"):
        j_authors = st.text_input("Authors (comma separated)")
        j_year = st.text_input("Year")
        art_title = st.text_input("Article Title")
        jou_title = st.text_input("Journal Title")
        vol = st.text_input("Volume")
        iss = st.text_input("Issue/Part")
        pgs = st.text_input("Page Numbers")
        submit_journal = st.form_submit_button("Generate & Add to List")

    if submit_journal:
        auth_list = [a.strip() for a in j_authors.split(",")]
        result = generate_journal_reference(auth_list, j_year, art_title, jou_title, vol, iss, pgs)
        st.session_state.bibliography.append(result)
        st.success("Reference added!")
        st.markdown(f"> {result}")

# --- TAB 3: WEBSITE ---
with tab3:
    st.header("Website Reference")
    with st.form("web_form"):
        w_authors = st.text_input("Author or Organisation")
        w_year = st.text_input("Year published or updated")
        w_title = st.text_input("Page Title")
        url = st.text_input("URL")
        access = st.text_input("Date Accessed")
        submit_web = st.form_submit_button("Generate & Add to List")

    if submit_web:
        auth_list = [a.strip() for a in w_authors.split(",")]
        result = generate_website_reference(auth_list, w_year, w_title, url, access)
        st.session_state.bibliography.append(result)
        st.success("Reference added!")
        st.markdown(f"> {result}")

# --- TAB 4: BIBLIOGRAPHY ---
with tab4:
    st.header("Final Bibliography")
    if not st.session_state.bibliography:
        st.info("Your bibliography is empty.")
    else:
        st.session_state.bibliography.sort(key=get_sort_key)
        for ref in st.session_state.bibliography:
            st.markdown(f"- {ref}")
        
        if st.button("Clear List"):
            st.session_state.bibliography = []
            st.rerun()

        # Word Export
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

# --- TAB 5: ESSAY AUDIT ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    st.write("Upload your essay to check for in-text citations.")
    
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx")
    
    if uploaded_file:
        doc = Document(uploaded_file)
        full_text = " ".join([para.text for para in doc.paragraphs])
        
        # Regex to find (Author, Year) or (Author Year)
        citations_found = re.findall(r'\(([^)]+ \d{4})\)', full_text)
        
        if citations_found:
            st.success(f"Found {len(citations_found)} potential in-text citations!")
            unique_cites = sorted(list(set(citations_found)))
            for cite in unique_cites:
                st.info(f"Detected: {cite}")
        else:
            st.warning("No standard in-text citations detected in this document.")

# --- MCL FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey; font-size: 0.8em;'>"
    "© 2026 Macmillan Centre for Learning. "
    "<a href='https://www.macmillancentreforlearning.co.uk/home-2/' target='_blank' style='color: #007bff; text-decoration: none;'>"
    "Go to Macmillan Centre for Learning</a>"
    "</div>", 
    unsafe_allow_html=True
)
