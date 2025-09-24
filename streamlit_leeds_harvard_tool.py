# streamlit_leeds_harvard_tool.py
import streamlit as st
import re
import requests
from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from docx.shared import Pt
from io import BytesIO
import fitz  # PyMuPDF
import textwrap
from urllib.parse import urlparse
import json
from datetime import datetime
from pathlib import Path
# ==========================
# Page config + CSS (colour scheme from your brief)
# ==========================
st.set_page_config(page_title="Leeds Harvard Referencing Tool",
                   page_icon="📚",
                   layout="wide")
# Global CSS for consistent colours and font sizing
st.markdown(
    f"""
    <style>
        :root {{
            --bg: #e6f7f8;             /* Background */
            --header-bg: #00a2b3;      /* Header Background */
            --header-text: #ffffff;    /* Header Text */
            --quiz-title: #008080;
            --question-box: #dff7f9;
            --button-bg: #009688;
            --accent-warm: #f9a825;
            --accent-cool: #5c6bc0;
            --muted-text: #37474f;
            --border: #80cbc4;
            --hover: #00796b;
            --secondary-bg: #f1f8e9;
            --highlight: #ffccbc;
            --link: #0288d1;
        }}
body {{
            background-color: var(--bg);
            color: var(--muted-text);
        }}
.header-container {{
            background-color: var(--header-bg);
            padding: 8px 14px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 18px;
        }}
        .header-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 6px;
        }}
.ref-box {{
            background: white;
            border: 1px solid var(--border);
            padding: 12px;
            border-radius: 8px;
        }}
.small-muted {{
            font-size:12px;
            color: #5f6b6b;
        }}
    </style>
    """,
    unsafe_allow_html=True
)
# ==========================
# Header (image stored at assets/Header.png)
# ==========================
st.markdown(
    """
    <div class="header-container">
        <img src="assets/Header.png" alt="Macmillan Centre for Learning Header">
    </div>
    """,
    unsafe_allow_html=True,
)
# Short intro and helpful links (open in new tab)
st.markdown(
    """
    <div style="margin-bottom:12px;">
    <strong>Leeds Harvard Referencing Checker & Guide</strong> — guidance and checks to help students learn Leeds Harvard referencing (not an automatic fixer; will explain required amendments).
    </div>
    <div class="small-muted">
    Example Leeds Harvard book entry: <em>Smith, J. 2023. Education in Practice. London: Routledge.</em>
    &nbsp;|&nbsp;
    <a href="https://library.leeds.ac.uk/info/1404/referencing/46/harvard_style" target="_blank" rel="noopener">Leeds University Library guidance</a>
    &nbsp;|&nbsp;
    <a href="https://www.maclearning.org" target="_blank" rel="noopener">Macmillan Centre for Learning</a>
    </div>
    """,
    unsafe_allow_html=True,
)
# ==========================
# Session state: references list
# ==========================
if "references" not in st.session_state:
    st.session_state.references = []  # list of dicts: {authors, year, title, source, url, notes}
# ==========================
# Helper functions
# ==========================
def surname_key(ref):
    """Return primary sorting key (surname of first author) for alphabetical ordering."""
    authors = ref.get("authors", "") or ""
    # If authors like "Smith, J." or "Smith J", pick first token before comma or space
    if "," in authors:
        surname = authors.split(",")[0].strip().lower()
    else:
        surname = authors.split()[0].strip().lower() if authors else ""
    return surname
def format_display_reference(ref):
    """
    Return a display-safe HTML/Markdown string of the Leeds Harvard formatted ref,
    with title italicised only.
    """
    authors = ref.get("authors", "").strip()
    year = ref.get("year", "").strip()
    title = ref.get("title", "").strip()
    source = ref.get("source", "").strip()
    url = ref.get("url", "").strip()
# Build base: Authors Year. Title. Source.
    parts = []
    if authors:
        parts.append(f"{authors}")
    if year:
        parts.append(f"{year}")
    header = ". ".join(parts).strip()
    if header:
        header = header + ". "
# Italicise title in Markdown: *title*
    title_md = f"*{title}*" if title else ""
    # Compose remainder
    remainder = ""
    if source:
        remainder = f" {source}."
    if url:
        remainder += f' <a href="{url}" target="_blank" rel="noopener">{url}</a>'
return f"{header}{title_md}{remainder}"
def parse_reference_string(s):
    """
    Heuristic parser. Input: single reference string (free text).
    Returns dict with keys: authors, year, title, source, url.
    Not perfect — uses simple heuristics but good enough to teach students.
    """
    s = s.strip()
    parsed = {"raw": s, "authors": "", "year": "", "title": "", "source": "", "url": ""}
    # Extract URL if any
    url_match = re.search(r"(https?://\S+)", s)
    if url_match:
        parsed["url"] = url_match.group(1).rstrip(".,)")
        s = s.replace(url_match.group(1), "").strip()
# Find year (4-digit)
    year_match = re.search(r"\b(19|20)\d{2}\b", s)
    if year_match:
        parsed["year"] = year_match.group(0)
        # remove year placeholder from string for simpler parsing
        s = s.replace(year_match.group(0), "").strip(". ,")
# Split on full stops to guess author/title/source
    parts = [p.strip() for p in re.split(r"\.\s+", s) if p.strip()]
    # Common Leeds Harvard pattern: Author. Year. Title. Place: Publisher.
    if len(parts) >= 1:
        # First part often contains author(s)
        if re.search(r"[A-Za-z]+,\s*[A-Z]", parts[0]) or re.search(r"\band\b", parts[0], re.I):
            parsed["authors"] = parts[0]
            if len(parts) >= 2:
                # Next part often title or year — but year possibly removed already
                # If remaining parts >=2, choose next as title
                parsed["title"] = parts[1] if len(parts) >= 2 else ""
                # source is remainder
                parsed["source"] = " ".join(parts[2:]) if len(parts) >= 3 else ""
        else:
            # If first part doesn't look like author, maybe it's title-first source (webpages)
            parsed["title"] = parts[0]
            parsed["source"] = " ".join(parts[1:]) if len(parts) >= 2 else ""
    # Final cleanup
    parsed = {k: v.strip() for k, v in parsed.items()}
    return parsed
def check_reference_for_leeds_harvard(parsed):
    """
    Check the parsed fields and return a list of suggested amendments.
    The function purposefully does NOT modify the reference—only suggests.
    """
    suggestions = []
    # Authors check
    if not parsed.get("authors"):
        suggestions.append("Add author(s): Leeds Harvard begins with surname then initials (e.g. Smith, J.).")
    # Year
    year = parsed.get("year", "")
    if not year:
        suggestions.append("Add year of publication (4-digit). Use 'n.d.' if no date is available.")
    else:
        if not re.match(r"^(19|20)\d{2}$", year):
            suggestions.append("Year looks unusual; ensure it is a 4-digit year (e.g. 2023).")
    # Title
    title = parsed.get("title", "")
    if not title:
        suggestions.append("Add the title of the work. In Leeds Harvard the title is italicised in the reference list.")
    # Source / Publisher
    source = parsed.get("source", "")
    url = parsed.get("url","")
    if url:
        # For web resources, source may be website name; include Accessed date
        suggestions.append("For websites include the main site or organisation and an accessed date (e.g. Accessed: 01 January 2025).")
    else:
        if not source:
            suggestions.append("Add place and publisher for books (e.g. London: Routledge) or the journal title/volume for articles.")
    return suggestions
def add_reference_to_session(parsed):
    """Add parsed reference dict to session_state.references, avoid duplicates by raw string."""
    raw = parsed.get("raw", "")
    # Avoid duplicates
    for r in st.session_state.references:
        if r.get("raw","").strip().lower() == raw.strip().lower():
            st.warning("This reference appears to already be in the list.")
            return False
    st.session_state.references.append(parsed)
    # Keep references alphabetically sorted for display (by surname)
    st.session_state.references.sort(key=surname_key)
    return True
def extract_text_from_docx_file(uploaded_file):
    """Extract text from uploaded .docx file object (uploaded_file is a file-like object)."""
    try:
        uploaded_file.seek(0)
        doc = DocxDocument(uploaded_file)
        paragraphs = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
        return "\n".join(paragraphs)
    except Exception:
        # Fallback: try reading bytes and use docx2txt (if available)
        try:
            uploaded_file.seek(0)
            import docx2txt
            tmp = BytesIO(uploaded_file.read())
            # docx2txt expects filename; write to temp file
            path = Path("temp_uploaded.docx")
            path.write_bytes(tmp.getvalue())
            txt = docx2txt.process(str(path))
            path.unlink(missing_ok=True)
            return txt
        except Exception as e:
            return f"[Error reading DOCX: {e}]"
def extract_text_from_pdf_file(uploaded_file):
    try:
        uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = []
        for page in doc:
            text.append(page.get_text())
        return "\n".join(text)
    except Exception as e:
        return f"[Error reading PDF: {e}]"
def find_reference_section(text):
    """
    Try to locate a 'References' or 'Reference list' section and return the lines that follow.
    """
    if not text:
        return []
    # Normalize and split into lines
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    # Find index of a heading likely to be references
    idx = None
    for i, ln in enumerate(lines):
        if re.match(r"^(references|reference list|bibliography)\b", ln, re.I):
            idx = i + 1
            break
    if idx is None:
        # Could be a list at the end without heading; attempt to heuristically find long list of lines with years or publisher patterns
        # We return an empty list so UI can ask for manual paste if not found.
        return []
    # Collect subsequent lines until a new heading (all caps or short)
    ref_lines = []
    for ln in lines[idx:]:
        # stop if next big heading
        if len(ln) < 60 and ln.isupper() and not re.search(r"\d", ln):
            break
        ref_lines.append(ln)
    return ref_lines

# docx hyperlink helper (creates a clickable hyperlink in python-docx)
# docx hyperlink helper (creates a clickable hyperlink in python-docx)
def add_hyperlink(paragraph, url, text, color="0000FF", underline=True):
    """
    Add a hyperlink to a python-docx paragraph.
    Returns the rId (relationship id) for testing if needed.
    """
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.opc.constants import RELATIONSHIP_TYPE as RT

    part = paragraph.part
    r_id = part.relate_to(url, RT.HYPERLINK, is_external=True)

    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')

    # Styling
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
from datetime import datetime

def generate_docx_reference_list(refs, accessed_date):
    """
    Build a .docx bytes buffer containing an alphabetised reference list with titles italicised,
    URLs as active links, and learner-supplied access date.
    Returns bytes buffer.
    """
    doc = DocxDocument()
    doc.add_heading("Reference List", level=1)

    # Sort alphabetically by surname
    sorted_refs = sorted(refs, key=surname_key)
    for r in sorted_refs:
        p = doc.add_paragraph()
        authors = r.get("authors", "")
        year = r.get("year", "")
        title = r.get("title", "")
        source = r.get("source", "")
        url = r.get("url", "")

        # Authors + Year
        if authors or year:
            p.add_run(f"{authors} ({year}). ")

        # Italicise title
        if title:
            run = p.add_run(title + ". ")
            run.italic = True

        # Source
        if source:
            p.add_run(source + ". ")

        # URL + accessed date (as per Leeds Harvard)
        if url:
            p.add_run("Available at: ")
            add_hyperlink(p, url, url)   # live hyperlink
            if accessed_date:
                p.add_run(f" (Accessed: {accessed_date}).")

    # Save to buffer
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def scan_document_for_citations_and_mismatch(text, references):
    """
    Basic check: find in-text citation patterns in the text, then compare to reference surnames.
    Returns dict with:
      - found_citations: set of surnames found in-text (from patterns)
      - referenced_surnames: set extracted from references
      - missing_in_refs: citations in text not in reference list
      - not_cited_in_text: references present but not cited in text
    """
    if not text:
        return {}
    # find friendlier citation patterns: (Surname, 2020) or Surname (2020)
    found = set()
    # pattern for (Author, 2020)
    for m in re.finditer(r"\(([^(),\d]+?),\s*(19|20)\d{2}\)", text):
        surname = m.group(1).strip().split()[-1]
        found.add(surname.lower())
    # pattern for Surname (2020)
    for m in re.finditer(r"\b([A-Z][a-zA-Z-]+)\s*\((19|20)\d{2}\)", text):
        surname = m.group(1).strip()
        found.add(surname.lower())

    # reference surnames
    ref_surnames = set()
    for r in references:
        auth = r.get("authors", "")
        if "," in auth:
            surname = auth.split(",")[0].strip()
        else:
            surname = auth.split()[0] if auth else ""
        if surname:
            ref_surnames.add(surname.lower())

    missing_in_refs = sorted(list(found - ref_surnames))
    not_cited = sorted(list(ref_surnames - found))

    return {
        "found_citations": sorted(list(found)),
        "referenced_surnames": sorted(list(ref_surnames)),
        "missing_in_refs": missing_in_refs,
        "not_cited_in_text": not_cited
    }

# ==========================
# UI layout: left = inputs, right = reference list
# ==========================
left_col, right_col = st.columns([2, 3])
with left_col:
    st.subheader("Input & Checks")
    input_mode = st.selectbox("Input method", ["Manual reference", "URL (webpage)", "Upload document (assessment/check)"])
if input_mode == "Manual reference":
        raw_ref = st.text_area("Paste or type the reference (one item). Example: Smith, J. 2023. Education in Practice. London: Routledge.", height=120)
        if st.button("Analyse reference"):
            if not raw_ref.strip():
                st.warning("Please paste or type a reference first.")
            else:
                parsed = parse_reference_string(raw_ref)
                st.session_state.last_parsed = parsed
                st.markdown("**Parsed fields:**")
                st.json(parsed)
                # validation suggestions
                suggestions = check_reference_for_leeds_harvard(parsed)
                if suggestions:
                    st.markdown("**Suggested amendments (student should act on these):**")
                    for s in suggestions:
                        st.info(s)
                else:
                    st.success("Reference looks well-formed for Leeds Harvard.")
                if st.button("Add this reference to Reference List"):
                    added = add_reference_to_session(parsed)
                    if added:
                        st.success("Reference added.")
    elif input_mode == "URL (webpage)":
        url_input = st.text_input("Enter the full webpage URL (https...)")
        if st.button("Fetch & suggest reference"):
            if not url_input.strip():
                st.warning("Enter a URL.")
            else:
                try:
                    meta = {}
                    r = requests.get(url_input, timeout=8)
                    s = BeautifulSoup(r.text, "html.parser")
                    title = s.title.string.strip() if s.title and s.title.string else ""
                    site = urlparse(url_input).netloc
                    parsed = {
                        "raw": f"{site} (n.d.) {title}. {url_input}",
                        "authors": site,
                        "year": "n.d.",
                        "title": title,
                        "source": site,
                        "url": url_input
                    }
                    st.json(parsed)
                    sug = check_reference_for_leeds_harvard(parsed)
                    if sug:
                        st.markdown("**Suggested amendments:**")
                        for s in sug:
                            st.info(s)
                    else:
                        st.success("Looks good.")
                    if st.button("Add webpage reference"):
                        add_reference_to_session(parsed)
                        st.success("Web reference added to Reference List.")
                except Exception as e:
                    st.error(f"Error fetching URL: {e}")
else:  # Upload
        st.markdown("Upload a student's assessment or a file containing references.")
        upload_file = st.file_uploader("Upload .docx or .pdf", type=["docx", "pdf"])
        if upload_file is not None:
            st.info("File uploaded. Extracting text (may take a few seconds).")
            if upload_file.type == "application/pdf":
                txt = extract_text_from_pdf_file(upload_file)
            else:
                txt = extract_text_from_docx_file(upload_file)
            # show small excerpt and allow the user to extract reference lines
            st.markdown("**Preview (first 800 chars)**")
            st.text(textwrap.shorten(txt, width=800, placeholder="..."))
            refs_found = find_reference_section(txt)
            if refs_found:
                st.markdown("**References section detected.** Example lines (first 20):")
                for ln in refs_found[:20]:
                    st.write(ln)
                if st.button("Parse these reference lines and add to Reference List"):
                    count = 0
                    for ln in refs_found:
                        parsed = parse_reference_string(ln)
                        add_reference_to_session(parsed)
                        count += 1
                    st.success(f"Added {count} references from the document.")
            else:
                st.warning("No 'References' heading detected automatically. You can copy/paste the reference list into Manual reference input or paste below.")
                pasted = st.text_area("Paste the reference list from the document here (one per line):", height=180)
                if st.button("Parse pasted references and add"):
                    lines = [l.strip() for l in pasted.splitlines() if l.strip()]
                    for ln in lines:
                        parsed = parse_reference_string(ln)
                        add_reference_to_session(parsed)
                    st.success(f"Parsed & added {len(lines)} references.")
with right_col:
    st.subheader("Reference List (Leeds Harvard)")
    # Reference list controls
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("Save references (JSON)"):
            # prepare JSON bytes
            js = json.dumps(st.session_state.references, indent=2)
            st.download_button("Download JSON", data=js, file_name="references.json", mime="application/json")
    with c2:
        if st.button("Export to Word (.docx)"):
            if not st.session_state.references:
                st.warning("Reference list is empty.")
            else:
                docx_buf = generate_docx_reference_list(st.session_state.references)
                st.download_button("Download Reference List (.docx)", data=docx_buf.getvalue(),
                                   file_name="Reference_List.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    with c3:
        if st.button("Clear references"):
            st.session_state.references = []
            st.success("Reference list cleared.")
st.markdown("---")
    if st.session_state.references:
        # Display references in alphabetical order
        for r in sorted(st.session_state.references, key=surname_key):
            st.markdown(format_display_reference(r), unsafe_allow_html=True)
    else:
        st.info("Reference list is empty. Add parsed references from the left-hand panel or upload a document.")
st.markdown("---")
    st.subheader("Checks on uploaded assessment")
    st.write("Upload the same student assessment (DOCX or PDF) to run a quick citation vs reference-list check.")
    check_file = st.file_uploader("Upload assessment to check", type=["docx", "pdf"], key="check_file")
    if check_file is not None:
        if check_file.type == "application/pdf":
            full_text = extract_text_from_pdf_file(check_file)
        else:
            full_text = extract_text_from_docx_file(check_file)
        st.write("Analyzing document...")
        results = scan_document_for_citations_and_mismatch(full_text, st.session_state.references)
        if not results:
            st.info("No textual content could be extracted for checks.")
        else:
            st.markdown("**In-text citations detected (sample):**")
            st.write(results.get("found_citations", []))
            if results.get("missing_in_refs"):
                st.error("Citations in text that are NOT present in the reference list:")
                for s in results["missing_in_refs"]:
                    st.write(f"- {s} — student should add a full Leeds Harvard reference in the list.")
            else:
                st.success("All detected in-text surnames appear in the reference list.")
            if results.get("not_cited_in_text"):
                st.warning("References in the list that were NOT found as citations in the document (possible unused references):")
                for s in results["not_cited_in_text"]:
                    st.write(f"- {s} — check whether this was cited in the assessment or remove it.")
# ==========================
# End of app: small footer and credits
# ==========================
st.markdown("---")
st.markdown(
    """
    <div class="small-muted">
    This tool is educational: it identifies missing components for Leeds Harvard referencing and tells students what they should change. 
    It does not automatically reformat students' work — that is intentional so students learn the conventions.  
    <br><br>
    For Leeds Harvard exact conventions, see Leeds University Library: 
    <a href="https://library.leeds.ac.uk/info/1404/referencing/46/harvard_style" 
    target="_blank" rel="noopener">Leeds Harvard guidance</a>.
    </div>
    """,
    unsafe_allow_html=True
)

# --- Fixed footer with copyright and logo ---
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #00a2b3;
        color: white;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        z-index: 100;
    }
    .footer img {
        height: 20px;
        vertical-align: middle;
        margin-right: 8px;
    }
    .footer a {
        color: #ffffff;
        text-decoration: none;
        font-weight: bold;
    }
    </style>
    <div class="footer">
        <img src="assets/logo-circle.png" alt="Logo">
        © 2025 <a href="https://macmillancentreforlearning.co.uk" target="_blank">
        Macmillan Centre for Learning</a>
    </div>
    """,
    unsafe_allow_html=True
)

