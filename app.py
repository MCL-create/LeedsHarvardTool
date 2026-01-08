import streamlit as st
from io import BytesIO
from docx import Document
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference, get_sort_key

# Page Config
st.set_page_config(page_title="Leeds Harvard Pro Tool", page_icon="📚")

# Initialize Bibliography Storage
if 'bibliography' not in st.session_state:
    st.session_state.bibliography = []

st.title("📚 Leeds Harvard Pro Tool")
st.write("Generate accurate references and download your full bibliography.")

# Tabs
tab1, tab2, tab3, tab_final = st.tabs(["📖 Book", "📰 Journal Article", "🌐 Website", "📋 My Bibliography"])

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
            st.success("Reference added to your Bibliography tab!")
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
        st.success("Reference added to your Bibliography tab!")
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
        st.success("Reference added to your Bibliography tab!")
        st.markdown(f"> {result}")

# --- TAB 4: THE BIBLIOGRAPHY EXPORT ---
with tab_final:
    st.header("Final Bibliography")
    if not st.session_state.bibliography:
        st.info("Your bibliography is empty. Generate references in the other tabs to see them here.")
    else:
        # Strict Sorting using the get_sort_key
        st.session_state.bibliography.sort(key=get_sort_key)
        
        for ref in st.session_state.bibliography:
            st.markdown(f"- {ref}")
        
        if st.button("Clear List"):
            st.session_state.bibliography = []
            st.rerun()

        # Generate Word Doc with Italics Preservation
        doc = Document()
        doc.add_heading('Bibliography', 0)
        
        for ref in st.session_state.bibliography:
            p = doc.add_paragraph()
            # This logic splits the string by * and turns italics back on for those parts
            parts = ref.split('*')
            for index, part in enumerate(parts):
                run = p.add_run(part)
                if index % 2 != 0: 
                    run.italic = True
        
        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        st.download_button(
            label="📥 Download as Word (.docx)",
            data=buffer,
            file_name="Leeds_Harvard_Bibliography.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
