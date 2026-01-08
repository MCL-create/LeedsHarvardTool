import streamlit as st
from leeds_harvard_tool import generate_book_reference, generate_journal_reference, generate_website_reference

# Page Config
st.set_page_config(page_title="Leeds Harvard Referencing Tool", page_icon="📚")

st.title("📚 Leeds Harvard Referencing Tool")
st.write("Generate accurate references following the University of Leeds Harvard style.")

# Create tabs for different reference types
tab1, tab2, tab3 = st.tabs(["📖 Book", "📰 Journal Article", "🌐 Website"])

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
        
        submit_book = st.form_submit_button("Generate Book Reference")

    if submit_book:
        if authors and year and title:
            auth_list = [a.strip() for a in authors.split(",")]
            result = generate_book_reference(auth_list, year, title, publisher, place, edition)
            st.success("Reference Generated:")
            st.markdown(f"> {result}")
            st.code(result.replace("*", ""), language=None) # Plain text version for easy copy
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
        pgs = st.text_input("Page Numbers", placeholder="e.g. 10-25")
        
        submit_journal = st.form_submit_button("Generate Journal Reference")

    if submit_journal:
        auth_list = [a.strip() for a in j_authors.split(",")]
        result = generate_journal_reference(auth_list, j_year, art_title, jou_title, vol, iss, pgs)
        st.success("Reference Generated:")
        st.markdown(f"> {result}")

# --- TAB 3: WEBSITE ---
with tab3:
    st.header("Website Reference")
    with st.form("web_form"):
        w_authors = st.text_input("Author or Organisation")
        w_year = st.text_input("Year published or updated")
        w_title = st.text_input("Page Title")
        url = st.text_input("URL")
        access = st.text_input("Date Accessed", placeholder="e.g. 15 May 2024")
        
        submit_web = st.form_submit_button("Generate Website Reference")

    if submit_web:
        auth_list = [a.strip() for a in w_authors.split(",")]
        result = generate_website_reference(auth_list, w_year, w_title, url, access)
        st.success("Reference Generated:")
        st.markdown(f"> {result}")
