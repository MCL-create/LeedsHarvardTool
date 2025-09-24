import os
port = int(os.environ.get("PORT", 8501))
st.set_page_config(page_title="Leeds Harvard Referencing Tool")
os.environ["STREAMLIT_SERVER_PORT"] = str(port)

import streamlit as st
import requests, re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from io import BytesIO
from docx import Document as DocxDocument
from PyPDF2 import PdfReader
from datetime import datetime

# =====================================================
# --- Branding Header ---
# =====================================================
col1, col2 = st.columns([1, 5])
with col1:
    st.image("assets/logo-circle.png", width=80)  # Fixed width, no deprecation warning
with col2:
    st.markdown(
        "<h1 style='color:#00a2b3;'>Leeds Harvard Referencing Tool</h1>",
        unsafe_allow_html=True
    )

st.markdown(
    "A tool to generate and check Leeds Harvard style references.",
    unsafe_allow_html=True
)

# =====================================================
# --- Sidebar Input Mode Selector ---
# =====================================================
input_mode = st.sidebar.radio(
    "Select input mode:",
    [
        "Paste text",
        "Upload document (Word/PDF)",
        "URL (webpage)",
        "Manual book reference",
        "Manual journal article reference",
        "Manual report / grey literature reference",
        "Manual other reference"
    ]
)

# =====================================================
# --- Helper Functions ---
# =====================================================
def extract_text_from_docx(file):
    doc = DocxDocument(file)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_from_pdf(file):
    pdf = PdfReader(file)
    return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

def surname_key(ref):
    authors = ref.get("authors", "")
    if "," in authors:
        return authors.split(",")[0].strip().lower()
    return authors.split()[0].lower() if authors else ""

def add_hyperlink(paragraph, url, text, color="0000FF", underline=True):
    """Add a clickable hyperlink to a docx paragraph."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.opc.constants import RELATIONSHIP_TYPE as RT

    part = paragraph.part
    r_id = part.relate_to(url, RT.HYPERLINK, is_external=True)

    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')

    if color:
        c = OxmlElement('w:color')
        c.set(qn('w:val'), color)
        rPr.append(c)
    if underline:
        u = OxmlElement('w:u')
        u.set(qn('w:val'), 'single')
        rPr.append(u)

    new_run.append(rPr)
    text_elem = OxmlElement('w:t')
    text_elem.text = text
    new_run.append(text_elem)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

    return r_id

def generate_docx_reference_list(refs):
    """Build a .docx reference list with Leeds Harvard formatting and clickable URLs."""
    doc = DocxDocument()
    doc.add_heading("Reference List", level=1)
    sorted_refs = sorted(refs, key=surname_key)
    for r in sorted_refs:
        p = doc.add_paragraph()
        authors = r.get("authors", "")
        year = r.get("year", "")
        title = r.get("title", "")
        source = r.get("source", "")
        url = r.get("url", "")
        access_date = r.get("accessed", "")

        # Build runs
        p.add_run(f"{authors} {year}. ")
        if title:
            run = p.add_run(title + ". ")
            run.italic = True
        if source:
            p.add_run(source + ". ")
        if url:
            p.add_run("Available at: ")
            add_hyperlink(p, url, url)
            if access_date:
                p.add_run(f" [Accessed {access_date}].")
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# =====================================================
# --- Reference Storage ---
# =====================================================
if "references" not in st.session_state:
    st.session_state["references"] = []

# =====================================================
# --- Input Modes ---
# =====================================================
text_input = ""

if input_mode == "Paste text":
    text_input = st.text_area("Paste your text here", height=200)

elif input_mode == "Upload document (Word/PDF)":
    file = st.file_uploader("Upload a Word or PDF document", type=["docx", "pdf"])
    if file:
        if file.name.endswith(".docx"):
            text_input = extract_text_from_docx(file)
        elif file.name.endswith(".pdf"):
            text_input = extract_text_from_pdf(file)

elif input_mode == "URL (webpage)":
    url_input = st.text_input("Enter the full webpage URL (https...)")
    access_date = st.text_input("Enter date accessed (e.g., 24 September 2025)")
    if st.button("Fetch & suggest reference"):
        if not url_input.strip():
            st.warning("Enter a URL.")
        else:
            try:
                r = requests.get(url_input, timeout=8)
                s = BeautifulSoup(r.text, "html.parser")
                title = s.title.string.strip() if s.title and s.title.string else ""
                site = urlparse(url_input).netloc
                st.success(f"Suggested reference: {site} (n.d.) {title}. Available at: {url_input} [Accessed {access_date}]")
                st.session_state["references"].append({
                    "authors": site,
                    "year": "n.d.",
                    "title": title,
                    "source": site,
                    "url": url_input,
                    "accessed": access_date
                })
            except Exception as e:
                st.error(f"Could not fetch metadata: {e}")

elif input_mode == "Manual book reference":
    authors = st.text_input("Authors (Surname, Initials)")
    year = st.text_input("Year")
    title = st.text_input("Book title")
    publisher = st.text_input("Publisher")
    url = st.text_input("URL (if online)")
    access_date = st.text_input("Accessed date")
    if st.button("Add book reference"):
        st.session_state["references"].append({
            "authors": authors, "year": year, "title": title,
            "source": publisher, "url": url, "accessed": access_date
        })
        st.success("Book reference added.")

elif input_mode == "Manual journal article reference":
    authors = st.text_input("Authors (Surname, Initials)")
    year = st.text_input("Year")
    title = st.text_input("Article title")
    journal = st.text_input("Journal name")
    volume = st.text_input("Volume/Issue")
    pages = st.text_input("Pages")
    url = st.text_input("URL (if online)")
    access_date = st.text_input("Accessed date")
    if st.button("Add journal reference"):
        source = f"{journal}, {volume}, {pages}"
        st.session_state["references"].append({
            "authors": authors, "year": year, "title": title,
            "source": source, "url": url, "accessed": access_date
        })
        st.success("Journal reference added.")

elif input_mode == "Manual report / grey literature reference":
    authors = st.text_input("Author/Organisation")
    year = st.text_input("Year")
    title = st.text_input("Report title")
    org = st.text_input("Organisation")
    url = st.text_input("URL (if online)")
    access_date = st.text_input("Accessed date")
    if st.button("Add report reference"):
        st.session_state["references"].append({
            "authors": authors, "year": year, "title": title,
            "source": org, "url": url, "accessed": access_date
        })
        st.success("Report reference added.")

elif input_mode == "Manual other reference":
    authors = st.text_input("Authors/Organisation")
    year = st.text_input("Year")
    title = st.text_input("Title")
    source = st.text_input("Source/Publisher")
    url = st.text_input("URL (if online)")
    access_date = st.text_input("Accessed date")
    if st.button("Add reference"):
        st.session_state["references"].append({
            "authors": authors, "year": year, "title": title,
            "source": source, "url": url, "accessed": access_date
        })
        st.success("Reference added.")

# =====================================================
# --- Display Reference List + Export ---
# =====================================================
if st.session_state["references"]:
    st.subheader("Current Reference List")
    sorted_refs = sorted(st.session_state["references"], key=surname_key)
    for r in sorted_refs:
        line = f"{r['authors']} {r['year']}. {r['title']}. {r['source']}."
        if r.get("url"):
            line += f" Available at: {r['url']}"
            if r.get("accessed"):
                line += f" [Accessed {r['accessed']}]."
        st.write(line)

    # Export as Word
    docx_data = generate_docx_reference_list(st.session_state["references"])
    st.download_button(
        label="Download Reference List (Word)",
        data=docx_data,
        file_name="reference_list.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

# =====================================================
# --- Footer ---
# =====================================================
st.markdown(
    "<hr><p style='text-align:center; color:#37474f;'>© 2025 Macmillan Centre for Learning | Leeds Harvard Referencing Tool</p>",
    unsafe_allow_html=True
)
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8501))
    st.run(server_port=port)
