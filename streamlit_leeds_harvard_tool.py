import streamlit as st
import requests, re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from io import BytesIO
from docx import Document as DocxDocument
from PyPDF2 import PdfReader

# --- Branding Header ---
col1, col2 = st.columns([1, 5])
with col1:
    st.image("assets/logo-circle.png", width=80)
with col2:
    st.markdown("<h1 style='color:#00a2b3;'>Leeds Harvard Referencing Tool</h1>", unsafe_allow_html=True)

st.markdown("A tool to generate and check Leeds Harvard style references.", unsafe_allow_html=True)

# --- Sidebar Input Mode Selector ---
st.sidebar.header("Select Input Mode")
input_mode = st.sidebar.radio(
    "Choose how you want to provide text:",
    ["Paste Text", "Upload DOCX", "Upload PDF", "URL (webpage)"]
)

# --- Helper Functions ---
def extract_text_from_docx(file):
    doc = DocxDocument(file)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_from_pdf(file):
    pdf = PdfReader(file)
    return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

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

# --- Input Mode Handling ---
text_input = ""

if input_mode == "Paste Text":
    text_input = st.text_area("Paste your text here", height=200)

elif input_mode == "Upload DOCX":
    file = st.file_uploader("Upload a Word document (.docx)", type=["docx"])
    if file:
        text_input = extract_text_from_docx(file)

elif input_mode == "Upload PDF":
    file = st.file_uploader("Upload a PDF document (.pdf)", type=["pdf"])
    if file:
        text_input = extract_text_from_pdf(file)

elif input_mode == "URL (webpage)":
    url_input = st.text_input("Enter the full webpage URL (https...)")
    if st.button("Fetch & suggest reference"):
        if not url_input.strip():
            st.warning("Enter a URL.")
        else:
            try:
                r = requests.get(url_input, timeout=8)
                s = BeautifulSoup(r.text, "html.parser")
                title = s.title.string.strip() if s.title and s.title.string else ""
                site = urlparse(url_input).netloc
                st.success(f"Suggested reference: {site} (n.d.) {title}. Available at: {url_input}")
            except Exception as e:
                st.error(f"Could not fetch metadata: {e}")

# --- Display Captured Text (for paste/upload modes) ---
if text_input:
    st.subheader("Extracted Text")
    st.write(text_input[:1000] + ("..." if len(text_input) > 1000 else ""))
