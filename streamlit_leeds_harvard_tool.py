
"""
Leeds Harvard Referencing Tool - full integrated Streamlit app.

Requirements (example requirements.txt entries):
streamlit
python-docx
requests
beautifulsoup4
docx2txt
pymupdf
"""

import streamlit as st
import re
import requests
from bs4 import BeautifulSoup
from docx import Document
from docx.shared import Inches
from io import BytesIO
import docx2txt
import fitz  # PyMuPDF
import textwrap
from urllib.parse import urlparse

# ---------------------------------------------------------
# Helper: Add hyperlink to python-docx paragraph
# (Recipe adapted to create a clickable hyperlink in .docx)
# ---------------------------------------------------------
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def add_hyperlink(paragraph, url, text, color="0000FF", underline=True):
    """
    Add a hyperlink to a paragraph (python-docx).
    Returns the <w:r> run element for additional styling if needed.
    """
    # Create the w:hyperlink tag and set required attributes
    part = paragraph.part
    r_id = part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    # Create a run
    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")

    # style: color
    if color:
        color_elem = OxmlElement("w:color")
        color_elem.set(qn("w:val"), color)
        rPr.append(color_elem)

    # style: underline
    if underline:
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rPr.append(u)

    new_run.append(rPr)

    # create w:t and set the text
    text_elem = OxmlElement("w:t")
    text_elem.text = text
    new_run.append(text_elem)

    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return new_run


# ---------------------------------------------------------
# CrossRef & URL scraping helpers (autofill)
# ---------------------------------------------------------
CROSSREF_API = "https://api.crossref.org/works/"

def lookup_doi(doi):
    """
    Query CrossRef for metadata given a DOI.
    Returns a dict with keys: author, year, title, journal/publisher, volume, issue, pages, url
    """
    try:
        doi = doi.strip()
        if doi.lower().startswith("http"):
            # user pasted a DOI link; extract part after '/'
            doi = doi.split("doi.org/")[-1]
        url = CROSSREF_API + doi
        resp = requests.get(url, timeout=10, headers={"User-Agent": "LeedsHarvardTool/1.0 (mailto:youremail@example.org)"})
        if resp.status_code != 200:
            return None
        data = resp.json()["message"]
        # extract
        authors = []
        for a in data.get("author", []):
            given = a.get("given", "")
            family = a.get("family", "")
            if family and given:
                authors.append(f"{family}, {given[0]}.")
            elif family:
                authors.append(family)
        author_str = "; ".join(authors) if authors else data.get("publisher", "")
        year = ""
        if "issued" in data and "date-parts" in data["issued"] and data["issued"]["date-parts"]:
            year = str(data["issued"]["date-parts"][0][0])
        title = data.get("title", [""])[0]
        container = data.get("container-title", [""])[0]  # journal
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        pages = data.get("page", "")
        link = data.get("URL", "")
        return {
            "author": author_str,
            "year": year,
            "title": title,
            "container": container,
            "volume": volume,
            "issue": issue,
            "pages": pages,
            "url": link
        }
    except Exception as e:
        return None


def scrape_url_for_metadata(url):
    """
    Simple metadata scraping for a given URL.
    Extracts page title, possible authors (from meta), and publish date (from meta).
    This is best-effort only.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; LeedsHarvardTool/1.0)"}
        resp = requests.get(url, timeout=8, headers=headers)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        title = soup.title.string.strip() if soup.title else ""
        # meta author
        author = ""
        author_meta = soup.find("meta", {"name": "author"}) or soup.find("meta", {"property": "author"})
        if author_meta and author_meta.get("content"):
            author = author_meta["content"]
        # publish date common meta tags
        date = ""
        for attr in ["article:published_time", "og:updated_time", "published", "dc.date", "date"]:
            tag = soup.find("meta", {"property": attr}) or soup.find("meta", {"name": attr})
            if tag and tag.get("content"):
                date = tag["content"]
                break
        # Simplify year from date if possible
        year = ""
        if date:
            m = re.search(r"(19|20)\d{2}", date)
            if m:
                year = m.group(0)
        return {
            "author": author or urlparse(url).netloc,
            "year": year,
            "title": title,
            "url": url
        }
    except Exception:
        return None


# ---------------------------------------------------------
# Formatting helpers (Leeds Harvard style)
# Store references as structured dicts in session state
# ---------------------------------------------------------
def format_reference_str(ref):
    """
    Produce a display string with markdown-ish italics for the Streamlit UI.
    ref is a dict containing keys depending on type.
    """
    typ = ref.get("type", "book")
    author = ref.get("author", "").strip()
    year = ref.get("year", "").strip()
    title = ref.get("title", "").strip()
    if typ == "book":
        place = ref.get("place", "")
        publisher = ref.get("publisher", "")
        return f"{author} {year}. *{title}*. {place}: {publisher}."
    if typ == "chapter":
        editors = ref.get("editors", "")
        book_title = ref.get("book_title", "")
        place = ref.get("place", "")
        publisher = ref.get("publisher", "")
        pages = ref.get("pages", "")
        return f"{author} {year}. '{title}', in {editors} (ed.) *{book_title}*. {place}: {publisher}, {pages}."
    if typ == "journal":
        journal = ref.get("journal", "")
        volume = ref.get("volume", "")
        issue = ref.get("issue", "")
        pages = ref.get("pages", "")
        return f"{author} {year}. '{title}', *{journal}*, {volume}({issue}), pp. {pages}."
    if typ == "website":
        site = ref.get("site_name", "")
        url = ref.get("url", "")
        access = ref.get("access_date", "")
        # clickable link in UI will be added separately
        return f"{author} {year}. *{title}*. {site}. Available at: {url} (Accessed: {access})."
    if typ == "report":
        org = ref.get("org", "")
        place = ref.get("place", "")
        publisher = ref.get("publisher", "")
        return f"{org} {year}. *{title}*. {place}: {publisher}."
    if typ == "thesis":
        degree = ref.get("degree", "")
        uni = ref.get("university", "")
        return f"{author} {year}. *{title}*. {degree}. {uni}."
    return ""


def docx_add_reference(doc, ref, logo_path=None):
    """
    Add a single reference to a python-docx Document with proper formatting.
    Only the title is italicised using add_run().italic = True
    """
    p = doc.add_paragraph()
    typ = ref.get("type", "book")
    author = ref.get("author", "")
    year = ref.get("year", "")
    title = ref.get("title", "")
    # Build pieces so we can add runs with correct italics
    if typ == "book":
        place = ref.get("place", "")
        publisher = ref.get("publisher", "")
        p.add_run(f"{author} {year}. ")
        r = p.add_run(title)
        r.italic = True
        p.add_run(f". {place}: {publisher}.")
    elif typ == "journal":
        journal = ref.get("journal", "")
        volume = ref.get("volume", "")
        issue = ref.get("issue", "")
        pages = ref.get("pages", "")
        p.add_run(f"{author} {year}. '")
        p.add_run(title).italic = True
        p.add_run(f"', {journal}, {volume}({issue}), pp. {pages}.")
    elif typ == "website":
        site = ref.get("site_name", "")
        url = ref.get("url", "")
        access = ref.get("access_date", "")
        p.add_run(f"{author} {year}. ")
        p.add_run(title).italic = True
        p.add_run(f". {site}. Available at: ")
        # add hyperlink
        add_hyperlink(p, url, url)
        p.add_run(f" (Accessed: {access}).")
    elif typ == "chapter":
        editors = ref.get("editors", "")
        book_title = ref.get("book_title", "")
        place = ref.get("place", "")
        publisher = ref.get("publisher", "")
        pages = ref.get("pages", "")
        p.add_run(f"{author} {year}. '")
        p.add_run(title).italic = True
        p.add_run(f"', in {editors} (ed.) ")
        p.add_run(book_title).italic = True
        p.add_run(f". {place}: {publisher}, {pages}.")
    elif typ == "report":
        org = ref.get("org", "")
        place = ref.get("place", "")
        publisher = ref.get("publisher", "")
        p.add_run(f"{org} {year}. ")
        p.add_run(title).italic = True
        p.add_run(f". {place}: {publisher}.")
    elif typ == "thesis":
        degree = ref.get("degree", "")
        uni = ref.get("university", "")
        p.add_run(f"{author} {year}. ")
        p.add_run(title).italic = True
        p.add_run(f". {degree}. {uni}.")
    else:
        p.add_run(format_reference_str(ref))


# ---------------------------------------------------------
# Text extraction, citation detection and reporting
# ---------------------------------------------------------
def extract_text_from_file(uploaded):
    """Given an uploaded file (docx or pdf), return its plain text."""
    if uploaded.name.lower().endswith(".docx"):
        return docx2txt.process(uploaded)
    elif uploaded.name.lower().endswith(".pdf"):
        text = ""
        with fitz.open(stream=uploaded.read(), filetype="pdf") as pdf:
            for p in pdf:
                text += p.get_text()
        return text
    return ""


CITATION_PATTERN = r"\(([A-Z][A-Za-z\-\']+)(?: et al\.)?,\s*(\d{4})\)"  # e.g. (Smith, 2023) or (O'Neil, 2021)


def find_intext_citations(text):
    """Return list of tuples (AuthorSurname, Year) found in the text."""
    return re.findall(CITATION_PATTERN, text)


def sentence_highlights(text, references):
    """
    For each sentence, find citations and mark green/orange depending on match.
    Returns list of tuples (sentence, status_text, color).
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    ref_authors = [r.get("author", "").split(",")[0] for r in references]  # first surname token
    ref_years = [r.get("year", "") for r in references]

    highlights = []
    for s in sentences:
        matches = re.findall(CITATION_PATTERN, s)
        for author, year in matches:
            # try to match author surname ignoring case and punctuation
            matched = False
            for ra, ry in zip(ref_authors, ref_years):
                if ra and author.lower() in ra.lower() and ry == year:
                    matched = True
                    break
            if matched:
                highlights.append((s.strip(), f"✅ ({author}, {year}) correctly cited", "green"))
            else:
                highlights.append((s.strip(), f"⚠ ({author}, {year}) missing from reference list", "orange"))
    return highlights


def find_unused_references(citations, references):
    """Find references that don't appear in the citations list."""
    results = []
    for r in references:
        author = r.get("author", "")
        year = r.get("year", "")
        # compare using surname token
        surname = author.split(",")[0] if "," in author else author.split()[0]
        used = any(surname.lower() in a.lower() and year == y for a, y in citations)
        if not used:
            results.append((r, "❌ Not cited in text", "red"))
    return results


# ---------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------
st.set_page_config(page_title="Leeds Harvard Referencing Tool", layout="wide")
st.markdown("---")

# Header banner (full width)
try:
    st.image("Header.png", use_column_width=True)
except Exception:
    st.warning("Header.png not found in the working folder — place your banner image file in the same folder as this script and name it 'Header.png'.")

st.title("📚 Leeds Harvard Referencing Checker & Guide")
st.write("""Developed by Macmillan Centre for Learning — helpful guidance for students learning Leeds Harvard referencing.""")
st.markdown(
    """
    <div>
      <a href="https://www.macmillancentre.org" target="_blank">Macmillan Centre for Learning</a> ·
      <a href="https://www.sssc.uk.com/registration/codes-of-practice" target="_blank">SSSC Codes of Practice (2024)</a> ·
      <a href="https://library.leeds.ac.uk/skills/referencing" target="_blank">Leeds University Library — Harvard guidance</a>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# Initialise session state storage for structured references
if "refs" not in st.session_state:
    st.session_state["refs"] = []  # list of dicts

# Left column: add / autofill reference
left, right = st.columns([2, 3])
with left:
    st.subheader("➕ Add or Autofill Reference")
    autofill_input = st.text_input("Paste DOI (10...) or URL here for autofill (or leave blank)", value="")
    if st.button("Autofill from DOI/URL"):
        if autofill_input.strip():
            # determine DOI-like versus URL-like
            candidate = autofill_input.strip()
            data = None
            if candidate.lower().startswith("http"):
                # Try DOI inside URL first
                if "doi.org/" in candidate:
                    doi_part = candidate.split("doi.org/")[-1]
                    data = lookup_doi(doi_part)
                if not data:
                    # scrape metadata
                    data = scrape_url_for_metadata(candidate)
            else:
                # probably raw DOI
                data = lookup_doi(candidate)
            if data:
                # Pre-fill fields in the right column by storing in session:
                st.session_state["autofill"] = data
                st.success("Autofill successful — check and edit fields before adding.")
            else:
                st.error("Autofill failed (no metadata found). You can still enter details manually.")
        else:
            st.error("Please paste a DOI or URL first.")

    st.markdown("**Or enter details manually:**")

    # Manual entry fields
    typ = st.selectbox("Reference type", ["book", "chapter", "journal", "website", "report", "thesis"])
    # Pre-populate from autofill if available
    autofill = st.session_state.get("autofill", {})

    author_val = st.text_input("Author(s) — surname, Initial(s).", value=autofill.get("author", ""))
    year_val = st.text_input("Year", value=autofill.get("year", ""))
    title_val = st.text_input("Title", value=autofill.get("title", ""))
    # type-specific
    place_val = st.text_input("Place (for books/reports)", value=autofill.get("place", ""))
    publisher_val = st.text_input("Publisher", value=autofill.get("publisher", ""))
    editors_val = st.text_input("Editors (for chapters)", value="")
    book_title_val = st.text_input("Book title (for chapter)", value="")
    pages_val = st.text_input("Pages (e.g. 45-60)", value=autofill.get("pages", ""))
    journal_val = st.text_input("Journal name (for journal articles)", value=autofill.get("container", ""))
    volume_val = st.text_input("Volume", value=autofill.get("volume", ""))
    issue_val = st.text_input("Issue", value=autofill.get("issue", ""))
    site_name_val = st.text_input("Website/Organisation (for websites)", value=autofill.get("author", ""))
    url_val = st.text_input("URL (for website)", value=autofill.get("url", ""))
    access_val = st.text_input("Accessed date (e.g. 20 September 2025)", value="")
    org_val = st.text_input("Organisation (for reports)", value=autofill.get("author", ""))
    degree_val = st.text_input("Degree (for theses)", value="")
    uni_val = st.text_input("University (for theses)", value="")

    if st.button("Add reference to list"):
        # Validate minimal
        if not author_val or not year_val or not title_val:
            st.error("Please supply at least author, year and title.")
        else:
            r = {
                "type": typ,
                "author": author_val,
                "year": year_val,
                "title": title_val,
                "place": place_val,
                "publisher": publisher_val,
                "editors": editors_val,
                "book_title": book_title_val,
                "pages": pages_val,
                "journal": journal_val,
                "volume": volume_val,
                "issue": issue_val,
                "site_name": site_name_val,
                "url": url_val,
                "access_date": access_val,
                "org": org_val,
                "degree": degree_val,
                "university": uni_val
            }
            st.session_state["refs"].append(r)
            # clear autofill for next time
            if "autofill" in st.session_state:
                del st.session_state["autofill"]
            st.success("Reference added to the working list.")

with right:
    st.subheader("📖 Working Reference List (A–Z)")
    if st.session_state.get("refs"):
        # Sort by author surname
        sorted_refs = sorted(st.session_state["refs"], key=lambda x: x.get("author", "").lower())
        # display with clickable links opening in new tab
        for r in sorted_refs:
            display = format_reference_str(r)
            if r.get("url"):
                # show link icon that opens in new tab
                # we put the link at end and set target=_blank
                st.markdown(f"{display} <a href='{r.get('url')}' target='_blank'>🔗</a>", unsafe_allow_html=True)
            else:
                st.markdown(display)
        clear_col, export_col = st.columns(2)
        with clear_col:
            if st.button("🗑 Clear all references"):
                st.session_state["refs"] = []
                st.success("All references cleared.")
        with export_col:
            if st.button("💾 Export reference list to Word (.docx)"):
                # Build docx
                doc = Document()
                # Add logo banner at top of docx too (optional)
                try:
                    doc.add_picture("Header.png", width=Inches(6))
                except Exception:
                    pass
                doc.add_heading("Reference List", level=1)
                for rr in sorted_refs:
                    docx_add_reference(doc, rr)
                doc.add_paragraph(f"\nProduced with support from Macmillan Centre for Learning — https://www.macmillancentre.org")
                buffer = BytesIO()
                doc.save(buffer)
                buffer.seek(0)
                st.download_button("📥 Download Reference_List.docx", data=buffer, file_name="Reference_List.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.info("Your working reference list is empty — add or autofill a reference on the left.")

st.markdown("---")

# ---------------------------------------------------------
# Upload student assessment, scan and feedback section
# ---------------------------------------------------------
st.subheader("📤 Upload Assessment / Scan Document for References")
uploaded = st.file_uploader("Upload a student assignment (.docx or .pdf)", type=["docx", "pdf"])

if uploaded:
    st.info("Extracting text — please wait a moment for longer files.")
    text = extract_text_from_file(uploaded)
    if not text.strip():
        st.error("No text could be extracted from this file.")
    else:
        citations = find_intext_citations(text)
        highlights = sentence_highlights(text, st.session_state.get("refs", []))
        unused = find_unused_references(citations, st.session_state.get("refs", []))

        st.subheader("📊 Colour-coded Referencing Feedback")

        # show progress summary
        total_citations = len(citations)
        matched = sum(1 for h in highlights if "correctly cited" in h[1])
        missing = sum(1 for h in highlights if "missing from reference list" in h[1])
        unused_count = len(unused)

        st.write(f"Found {total_citations} in-text citation(s): {matched} matched, {missing} missing. Unused references: {unused_count}")
        st.progress(min(100, int((matched / total_citations * 100) if total_citations else 0)))

        # Display highlights color-coded
        for sentence, status, colour in highlights:
            # use small excerpt + color-coded label
            st.markdown(f"<div style='padding:8px;border-radius:6px;background:#f8f9fa;'><span style='color:{colour};font-weight:600'>{status}</span><br><span>{sentence}</span></div>", unsafe_allow_html=True)

        if unused:
            st.write("### ❌ Unused references (appear in reference list but not cited in text)")
            for r, status, colour in unused:
                st.markdown(f"<div style='padding:6px;background:#fff6f6;border-left:4px solid #ff4d4d'>{format_reference_str(r)} — <span style='color:{colour};'>{status}</span></div>", unsafe_allow_html=True)

        # Offer detailed report export
        if st.button("📥 Download detailed Referencing Report (Word)"):
            # Build report docx
            doc = Document()
            try:
                doc.add_picture("Header.png", width=Inches(6))
            except Exception:
                pass
            doc.add_heading("Referencing Report", level=1)
            doc.add_heading("In-text citations (sentence context)", level=2)
            for sentence, status, colour in highlights:
                p = doc.add_paragraph()
                p.add_run(textwrap.fill(sentence, 90))
                p.add_run("\n→ " + status)
            if unused:
                doc.add_heading("Unused references", level=2)
                for r, status, colour in unused:
                    p = doc.add_paragraph()
                    docx_add_reference(doc, r)
                    p.add_run(" — " + status)
            doc.add_paragraph(f"\nProduced with support from Macmillan Centre for Learning — https://www.macmillancentreforlearning.co.uk")
            buf = BytesIO()
            doc.save(buf)
            buf.seek(0)
            st.download_button("Download Referencing_Report.docx", data=buf, file_name="Referencing_Report.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

st.markdown("---")
st.caption("If you’d like, I can add DOI lookup fallback to other APIs (CrossRef is used now), or extend the in-text citation regex to support other citation formats — tell me which formats your students use most.")
=======
import streamlit as st
from leeds_harvard_tool import generate_reference  # this comes from your main tool

st.set_page_config(page_title="Leeds Harvard Referencing Tool", page_icon="📚", layout="centered")

st.title("📚 Leeds Harvard Referencing Checker & Guide")

st.markdown(
    """
    Use this tool to check and build Leeds Harvard references.  
    Enter the details below and the tool will show you the correct format.  
    This way you can learn how to structure your own references correctly.
    """
)

# Input fields for reference details
author = st.text_input("Author(s) (e.g., Smith, J.)")
year = st.text_input("Year (e.g., 2023)")
title = st.text_input("Title of Book/Article")
publisher = st.text_input("Publisher (if applicable)")
place = st.text_input("Place of Publication (if applicable)")

# Button to generate the reference
if st.button("Generate Reference"):
    if author and year and title:
        reference = generate_reference(author, year, title, publisher, place)
        st.success(f"✅ Your Leeds Harvard reference:\n\n{reference}")
        st.info("Tip: Compare this output with your own reference to see where you might need to amend it.")
    else:
        st.error("⚠️ Please fill in at least Author, Year, and Title.")

