import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import streamlit as st
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


# -----------------------------
# Utility Functions
# -----------------------------

def fetch_webpage_text(url):
    """Fetch text content from a webpage."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = [p.get_text() for p in soup.find_all("p")]
        return "\n".join(paragraphs)
    except Exception as e:
        return f"Error fetching webpage: {e}"


def extract_surnames(reference_list):
    """Extract surnames from references using a regex pattern."""
    surnames = []
    for ref in reference_list:
        match = re.match(r"([A-Z][a-zA-Z'`-]+)", ref)
        if match:
            surnames.append(match.group(1))
    return surnames


def check_in_text_citations(text, references):
    """Check which references are cited in the main text."""
    ref_surnames = set(extract_surnames(references))
    found = set()

    for surname in ref_surnames:
        if re.search(rf"\b{surname}\b", text):
            found.add(surname)

    not_cited = sorted(list(ref_surnames - found))
    return not_cited


def format_display_reference(ref, idx):
    """Format references for display with HTML links if a URL is present."""
    url_match = re.search(r"(https?://\S+)", ref)
    url = url_match.group(0) if url_match else None
    header = f"**[{idx}]** "
    title_md = ref.replace(url, "").strip() if url else ref.strip()
    remainder = ""

    if url:
        remainder += f' <a href="{url}" target="_blank" rel="noopener">{url}</a>'
    return f"{header}{title_md}{remainder}"


def add_hyperlink(paragraph, url, text):
    """Add a hyperlink to a paragraph in a Word document."""
    part = paragraph.part
    r_id = part.relate_to(url, relationshiptype="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")

    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)

    c = OxmlElement("w:color")
    c.set(qn("w:val"), "0000FF")
    rPr.append(c)

    new_run.append(rPr)
    text_elem = OxmlElement("w:t")
    text_elem.text = text
    new_run.append(text_elem)

    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

    return hyperlink


# -----------------------------
# Streamlit App
# -----------------------------

st.set_page_config(page_title="Leeds Harvard Referencing Tool", layout="wide")
st.title("📚 Leeds Harvard Referencing Checker")

st.markdown(
    "This tool helps you format and check your references using the **Leeds Harvard** style. "
    "You can paste text, upload a file, or provide a URL."
)

# Sidebar for input mode
st.sidebar.header("Input Options")
input_mode = st.sidebar.radio("Select input method:", ["Paste text", "Upload .docx file", "URL (webpage)"])

main_text = ""
references = []

if input_mode == "Paste text":
    main_text = st.text_area("Paste your main text here", height=250)
    references_text = st.text_area("Paste your reference list here (one per line)", height=200)
    if references_text:
        references = [ref.strip() for ref in references_text.split("\n") if ref.strip()]

elif input_mode == "Upload .docx file":
    uploaded_file = st.file_uploader("Upload a Word (.docx) file", type=["docx"])
    if uploaded_file:
        doc = Document(uploaded_file)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        if paragraphs:
            split_index = None
            for i, p in enumerate(paragraphs):
                if "reference" in p.lower():
                    split_index = i
                    break
            if split_index:
                main_text = "\n".join(paragraphs[:split_index])
                references = paragraphs[split_index + 1:]
            else:
                main_text = "\n".join(paragraphs)

elif input_mode == "URL (webpage)":
    url_input = st.text_input("Enter the webpage URL:")
    if url_input:
        main_text = fetch_webpage_text(url_input)


# -----------------------------
# Analysis and Results
# -----------------------------
if main_text:
    st.subheader("Analysis Results")

    if references:
        not_cited = check_in_text_citations(main_text, references)

        left_col, right_col = st.columns(2)

        with left_col:
            st.markdown("### 📄 Main Text Preview")
            st.write(main_text[:1000] + ("..." if len(main_text) > 1000 else ""))

        with right_col:
            st.markdown("### 📑 Reference List")
            if st.session_state.get("references") is None:
                st.session_state.references = references

            for idx, ref in enumerate(st.session_state.references, 1):
                st.markdown(format_display_reference(ref, idx), unsafe_allow_html=True)

            st.subheader("Checks:")
            if not_cited:
                st.warning(f"The following references were **not cited** in the text: {', '.join(not_cited)}")
            else:
                st.success("✅ All references appear to be cited in the text.")

    else:
        st.info("Please add or upload your references for analysis.")

# -----------------------------
# Export Options
# -----------------------------
st.sidebar.subheader("Export Options")

if st.sidebar.button("Download Results as Word (.docx)"):
    doc = Document()
    doc.add_heading("Analysis Results", 0)

    doc.add_heading("Main Text", level=1)
    doc.add_paragraph(main_text)

    if references:
        doc.add_heading("References", level=1)
        for idx, ref in enumerate(references, 1):
            url_match = re.search(r"(https?://\S+)", ref)
            url = url_match.group(0) if url_match else None
            p = doc.add_paragraph(f"[{idx}] ")
            if url:
                ref_text = ref.replace(url, "").strip()
                p.add_run(ref_text + " ")
                add_hyperlink(p, url, url)
            else:
                p.add_run(ref)

    st.sidebar.download_button(
        label="Download Word File",
        data=doc,
        file_name="referencing_results.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
