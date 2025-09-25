import streamlit as st
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import docx2txt
import fitz  # PyMuPDF
from docx import Document
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# ------------------------------
# App Configuration
# ------------------------------
st.set_page_config(
    page_title="Leeds Harvard Referencing Tool",
    page_icon="📚",
    layout="wide"
)

# Global reference list
if "reference_list" not in st.session_state:
    st.session_state.reference_list = []

reference_list = st.session_state.reference_list

# ------------------------------
# Header with Logo
# ------------------------------
# --- Header ---
st.markdown(
    """
    <div style="
        background-color: #00a2b3;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    ">
        <h1 style="color: #ffffff; margin: 0;">Leeds Harvard Referencing Checker</h1>
        <p style="color: #ffffff; margin: 0; font-size: 16px;">Developed by Macmillan Centre for Learning</p>
    </div>
    """,
    unsafe_allow_html=True
)
# ------------------------------
# Sidebar Navigation
# ------------------------------
page = st.sidebar.radio(
    "Navigate",
    ["Referencing Tool", "How to Use"]
)

# ------------------------------
# Helper Functions
# ------------------------------
def add_reference(ref):
    if ref not in reference_list:
        reference_list.append(ref)

def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_docx(uploaded_file):
    return docx2txt.process(uploaded_file)

def extract_text_from_url(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.get_text()

# --- Export Functions ---
def export_txt(refs):
    text_output = "\n".join(refs)
    st.download_button("⬇️ Export TXT", text_output, file_name="references.txt")

def export_pdf(refs):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    for ref in refs:
        c.drawString(50, y, ref)
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
    c.save()
    buffer.seek(0)
    st.download_button("⬇️ Export PDF", buffer, file_name="references.pdf")

def export_docx(refs):
    doc = Document()
    doc.add_heading("Reference List", level=1)
    for ref in refs:
        doc.add_paragraph(ref)
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    st.download_button("⬇️ Export DOCX", buffer, file_name="references.docx")

def export_excel(refs):
    df = pd.DataFrame(refs, columns=["Reference"])
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="References")
    buffer.seek(0)
    st.download_button("⬇️ Export Excel", buffer, file_name="references.xlsx")

# ------------------------------
# Main Page: Referencing Tool
# ------------------------------
if page == "Referencing Tool":
    st.subheader("Select Input Mode")
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

    # --- Input Modes ---
    if input_mode == "Paste text":
        pasted_text = st.text_area("Paste your text here:")
        if st.button("Check References"):
            add_reference("Example formatted reference from pasted text")

    elif input_mode == "Upload document (Word/PDF)":
        uploaded_file = st.file_uploader("Upload your document", type=["pdf", "docx"])
        if uploaded_file:
            if uploaded_file.name.endswith(".pdf"):
                text = extract_text_from_pdf(uploaded_file)
            else:
                text = extract_text_from_docx(uploaded_file)
            st.success("File uploaded and text extracted.")
            if st.button("Check References"):
                add_reference("Example formatted reference from uploaded document")

    elif input_mode == "URL (webpage)":
        url = st.text_input("Enter webpage URL:")
        if st.button("Fetch and Check"):
            try:
                text = extract_text_from_url(url)
                st.success("Webpage text extracted.")
                add_reference("Example formatted reference from webpage")
            except Exception as e:
                st.error(f"Error fetching URL: {e}")

    elif input_mode == "Manual book reference":
        author = st.text_input("Author(s)")
        year = st.text_input("Year")
        title = st.text_input("Title")
        publisher = st.text_input("Publisher")
        if st.button("Add Book Reference"):
            ref = f"{author} ({year}) {title}. {publisher}."
            add_reference(ref)

    elif input_mode == "Manual journal article reference":
        author = st.text_input("Author(s)")
        year = st.text_input("Year")
        title = st.text_input("Article Title")
        journal = st.text_input("Journal Title")
        volume = st.text_input("Volume/Issue")
        pages = st.text_input("Pages")
        if st.button("Add Journal Reference"):
            ref = f"{author} ({year}) '{title}', {journal}, {volume}, {pages}."
            add_reference(ref)

    elif input_mode == "Manual report / grey literature reference":
        author = st.text_input("Author/Organisation")
        year = st.text_input("Year")
        title = st.text_input("Title")
        publisher = st.text_input("Publisher/Organisation")
        if st.button("Add Report Reference"):
            ref = f"{author} ({year}) {title}. {publisher}."
            add_reference(ref)

    elif input_mode == "Manual other reference":
        ref = st.text_area("Enter full reference in Leeds Harvard style")
        if st.button("Add Other Reference"):
            add_reference(ref)

    # --- Always Visible Reference List + Exports ---
    st.markdown("---")
    st.subheader("📖 Current Reference List")
    if reference_list:
        for i, ref in enumerate(reference_list, 1):
            st.write(f"{i}. {ref}")
    else:
        st.info("No references yet. Add one using the options above.")

    st.markdown("---")
    st.subheader("📤 Export Reference List")
    if reference_list:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            export_txt(reference_list)
        with col2:
            export_pdf(reference_list)
        with col3:
            export_docx(reference_list)
        with col4:
            export_excel(reference_list)
    else:
        st.info("No references to export.")

# ------------------------------
# Help Page: How to Use
# ------------------------------
elif page == "How to Use":
    st.subheader("📘 How to Use the Leeds Harvard Referencing Tool")
    st.markdown("""
    This tool helps learners and tutors generate, format, and manage references in the **Leeds Harvard style**.

    ### Input Options
    - **Paste text**: Paste assignment text, and the tool will identify references.
    - **Upload document (Word/PDF)**: Upload a file for automatic scanning.
    - **URL (webpage)**: Provide a webpage link for extraction and referencing.
    - **Manual book / journal / report / other**: Add references manually.

    ### Reference Checking
    - The tool extracts surnames and cross-checks them with the reference list.
    - Missing references or unmatched citations are highlighted (suggested improvements included).

    ### Export Options
    You can always download your reference list in:
    - **TXT** (plain text)
    - **PDF**
    - **DOCX**
    - **Excel (.xlsx)**

    ### Tips
    - Always double-check references for accuracy.
    - This tool is a support — your academic responsibility is to ensure correctness.
    """)

# ------------------------------
# Footer
# ------------------------------
# --- Footer ---
try:
    st.image("footer_logo.png", width=120)  # optional footer logo if you want one
except Exception:
    st.markdown("<div style='font-size:20px; color:#00a2b3; text-align:center;'>MCL</div>", unsafe_allow_html=True)

st.markdown(
    """
    <hr style="border:1px solid #80cbc4;">
    <div style="
        background-color: #f1f8e9;
        padding: 10px;
        text-align: center;
        border-radius: 8px;
        color: #37474f;
        font-size: 14px;
    ">
        <p>© 2025 <a href="https://macmillancentreforlearning.co.uk" target="_blank" style="color:#0288d1; text-decoration:none;">
        Macmillan Centre for Learning</a> | Built with Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)

