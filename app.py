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
try:
    st.image("assets/Header.png", use_container_width=True)
except Exception:
    st.title("📚 Leeds Harvard Pro Tool")

# --- TABS DEFINITION ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📖 Book", "📰 Journal Article", "🌐 Website", "📋 My Bibliography", "🔍 Essay Audit"
])

# --- TAB 1, 2, 3 (Input Logic) ---
with tab1:
    st.header("Book Reference")
    with st.form("book_form"):
        authors = st.text_input("Authors (comma separated)", placeholder="e.g. Smith, J., Doe, R.")
        year = st.text_input("Year of Publication")
        title = st.text_input("Book Title")
        edition = st.text_input("Edition (leave blank if 1st)")
        place = st.text_input("Place of Publication")
        publisher = st.text_input("Publisher")
        if st.form_submit_button("Generate & Add to List"):
            if authors and year and title:
                res = generate_book_reference([a.strip() for a in authors.split(",")], year, title, publisher, place, edition)
                st.session_state.bibliography.append(res)
                st.success("Added to Bibliography!")
            else: st.error("Missing fields.")

with tab2:
    st.header("Journal Reference")
    with st.form("journal_form"):
        j_auth = st.text_input("Authors")
        j_yr = st.text_input("Year")
        a_tit = st.text_input("Article Title")
        j_tit = st.text_input("Journal Title")
        vol = st.text_input("Volume")
        iss = st.text_input("Issue")
        pgs = st.text_input("Pages")
        if st.form_submit_button("Generate & Add"):
            res = generate_journal_reference([a.strip() for a in j_auth.split(",")], j_yr, a_tit, j_tit, vol, iss, pgs)
            st.session_state.bibliography.append(res)
            st.success("Added!")

with tab3:
    st.header("Website Reference")
    with st.form("web_form"):
        w_auth = st.text_input("Author/Org")
        w_yr = st.text_input("Year")
        w_tit = st.text_input("Page Title")
        url = st.text_input("URL")
        acc = st.text_input("Date Accessed")
        if st.form_submit_button("Generate & Add"):
            res = generate_website_reference([a.strip() for a in w_auth.split(",")], w_yr, w_tit, url, acc)
            st.session_state.bibliography.append(res)
            st.success("Added!")

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
        st.download_button("📥 Download Bibliography (.docx)", buf.getvalue(), "Bibliography.docx")
        if st.button("Clear List"):
            st.session_state.bibliography = []
            st.rerun()

# --- TAB 5: UPDATED PRECISION ESSAY AUDIT ---
with tab5:
    st.header("🔍 Essay Citation Audit")
    uploaded_file = st.file_uploader("Upload Essay (.docx)", type="docx")
    
    if uploaded_file:
        doc = Document(uploaded_file)
        full_text = " ".join([p.text for p in doc.paragraphs])
        
        # IMPROVED REGEX: Limits length to 100 chars to avoid catching whole paragraphs
        # Specifically looks for: (AnyText 4-Digit-Year)
        citations_found = re.findall(r'\(([^)]{5,100}?\d{4}[^)]{0,20}?)\)', full_text)
        
        if citations_found:
            st.write(f"### Found {len(citations_found)} Citations")
            bib_joined = " ".join(st.session_state.bibliography).lower()
            
            audit_list = []
            for cite in sorted(list(set(citations_found))):
                # Check if the primary name exists in bibliography
                main_name = cite.split(',')[0].split(' ')[0].lower()
                is_missing = main_name not in bib_joined
                status = "⚠️ Missing from List" if is_missing else "✅ Matched"
                audit_list.append({"Citation Found": f"({cite})", "Status": status})
            
            st.table(audit_list)
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
