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
# We use a robust path and check if the file exists to prevent errors
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
            if j_authors and j_year:
                auth_list = [a.strip() for a in j_authors.split(",")]
                result = generate_journal_reference(auth_list, j_year, art_title, jou_title, vol, iss, pgs)
                st.session_state.bibliography.append(result)
                st.success("Reference added!")
                st.markdown(f"> {result}")
            else:
                st.error("Authors and Year are required.")

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
            if w_authors and w_year:
                auth_list = [a.strip() for a in w_authors.split(",")]
                result = generate_website_reference(auth_list, w_year, w_title, url, access)
                st.session_state.bibliography.append(result)
                st.success("Reference added!")
                st.markdown(f"> {result}")
            else:
                st.error("Author and Year are required.")

# --- TAB 4: BIBLIOGRAPHY ---
with tab4:
    st.header("Final Bibliography")
    if not st.session_state.bibliography:
        st.info("Your bibliography is empty. Generate references in other tabs first.")
    else:
        # Strict Alphabetical Sorting
        st.session_state.bibliography.sort(key=get_sort_key)
        for ref in st.session_state.bibliography:
            st.markdown(f"- {ref}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Entire List"):
                st.session_state.bibliography = []
                st.rerun()
        
        with col2:
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
            st.download_button("📥 Download as Word (.docx)", buffer, "MCL_Bibliography.docx")

# --- TAB 5: ESSAY AUDIT ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    st.write("Upload your essay (.docx) to check if your in-text citations match your bibliography.")
    
    # The file uploader
    uploaded_file = st.file_uploader("Choose your essay file", type="docx", key="essay_uploader")
    
    if uploaded_file is not None:
        # Display file details so you know it's attached
        st.info(f"📄 File attached: {uploaded_file.name}")
        
        if st.button("Analyze Essay Citations"):
            try:
                # Read the Word Document
                doc = Document(uploaded_file)
                paragraphs = [para.text for para in doc.paragraphs if para.text.strip() != ""]
                full_text = " ".join(paragraphs)
                
                # Regex: Looks for (Author Year) or (Author, Year) or (Author et al., Year)
                # This pattern is specifically tuned for Leeds Harvard
                citation_pattern = r'\(([^)]*\d{4}[^)]*)\)'
                citations_found = re.findall(citation_pattern, full_text)
                
                if citations_found:
                    st.success(f"Audit Complete: {len(citations_found)} citations detected.")
                    
                    # Create a comparison list
                    bib_content = " ".join(st.session_state.bibliography).lower()
                    audit_results = []
                    
                    for cite in sorted(list(set(citations_found))):
                        # Extract the first word (usually the Surname) to check against Bibliography
                        match_word = cite.split()[0].replace(',', '').lower()
                        
                        if match_word in bib_content:
                            status = "✅ Match Found"
                        else:
                            status = "⚠️ Missing from List"
                        
                        audit_results.append({"In-Text Citation": f"({cite})", "Status": status})
                    
                    st.table(audit_results)
                else:
                    st.warning("No citations were found. Ensure your citations are in brackets, e.g., (Smith, 2024).")
            
            except Exception as e:
                st.error(f"Error processing file: {e}")
    else:
        st.info("Please browse or drag and drop a .docx file to begin.")

# --- MCL FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey; font-size: 0.9em;'>"
    "© 2026 Macmillan Centre for Learning. <br>"
    "<a href='https://www.macmillancentreforlearning.co.uk/home-2/' target='_blank' style='color: #007bff; font-weight: bold; text-decoration: none;'>"
    "Go to Macmillan Centre for Learning</a>"
    "</div>", 
    unsafe_allow_html=True
)
