# streamlit_leeds_harvard_tool.py
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import streamlit as st
from docx import Document as DocxDocument
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from io import BytesIO
import textwrap
from pathlib import Path
import json
from datetime import datetime

# -----------------------------
# Page config + CSS (brand colours)
# -----------------------------
st.set_page_config(page_title="Leeds Harvard Referencing Tool",
                   page_icon="📚",
                   layout="wide")

st.markdown(
    """
    <style>
        :root {
            --bg: #e6f7f8;
            --header-bg: #00a2b3;
            --muted-text: #37474f;
            --border: #80cbc4;
            --link: #0288d1;
        }
        body { background-color: var(--bg); color: var(--muted-text); }
        .header-container {
            background-color: var(--header-bg);
            padding: 8px 14px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 18px;
        }
        .header-container img { max-width:100%; height:auto; border-radius:6px; }
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
        .footer img { height:20px; vertical-align: middle; margin-right:8px; }
        .footer a { color: #ffffff; text-decoration: none; font-weight: bold; margin-left:6px;}
        .ref-box { background: white; border: 1px solid var(--border); padding:12px; border-radius:8px; }
        .small-muted { font-size:12px; color:#5f6b6b; }
    </style>
    """,
    unsafe_allow_html=True
)

# Header
st.markdown(
    """
    <div class="header-container">
        <img src="assets/Header.png" alt="Macmillan Centre for Learning Header">
    </div>
    """,
    unsafe_allow_html=True
)

# Short intro
st.markdown(
    """
    <div style="margin-bottom:12px;">
    <strong>Leeds Harvard Referencing Checker & Guide</strong> — this tool identifies missing components for Leeds Harvard referencing and explains what students should change (it does not automatically reformat student work).
    </div>
    <div class="small-muted">
    Example Leeds Harvard book entry: <em>Smith, J. 2023. Education in Practice. London: Routledge.</em>
    &nbsp;|&nbsp;
    <a href="https://library.leeds.ac.uk/info/1404/referencing/46/harvard_style" target="_blank" rel="noopener">Leeds Harvard guidance</a>
    &nbsp;|&nbsp;
    <a href="https://macmillancentreforlearning.co.uk" target="_blank" rel="noopener">Macmillan Centre for Learning</a>
    </div>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# Session state
# -----------------------------
if "references" not in st.session_state:
    st.session_state.references = []  # list of dicts: authors,year,title,source,url,raw

# -----------------------------
# Helper functions
# -----------------------------
def surname_key(ref):
    authors = ref.get("authors", "") or ""
    if "," in authors:
        return authors.split(",")[0].strip().lower()
    else:
        return (authors.split()[0].strip().lower() if authors else "")

def format_display_reference(ref):
    """
    Return a display-safe HTML string of Leeds Harvard formatted ref with title italicised only.
    """
    authors = (ref.get("authors") or "").strip()
    year = (ref.get("year") or "").strip()
    title = (ref.get("title") or "").strip()
    source = (ref.get("source") or "").strip()
    url = (ref.get("url") or "").strip()

    parts = []
    if authors:
        parts.append(f"{authors}")
    if year:
        # show year with parentheses for display consistency
        parts.append(f"({year})")
    header = " ".join(parts).strip()
    if header:
        header = header + ". "

    title_md = f"<em>{title}</em>" if title else ""
    remainder = ""
    if source:
        remainder = f" {source}."
    if url:
        remainder += f' <a href="{url}" target="_blank" rel="noopener">{url}</a>'

    return f"{header}{title_md}{remainder}"

def parse_reference_string(s):
    """
    Heuristic parser for a free-text reference line.
    """
    s = (s or "").strip()
    parsed = {"raw": s, "authors": "", "year": "", "title": "", "source": "", "url": ""}
    if not s:
        return parsed

    # extract URL
    url_match = re.search(r"(https?://\S+)", s)
    if url_match:
        parsed["url"] = url_match.group(1).rstrip(".,)")
        s = s.replace(url_match.group(1), "").strip()

    # find year (19xx or 20xx)
    year_match = re.search(r"\b(19|20)\d{2}\b", s)
    if year_match:
        parsed["year"] = year_match.group(0)
        s = s.replace(year_match.group(0), "").strip(" .,")

    # split on full stop to break into parts
    parts = [p.strip() for p in re.split(r"\.\s+", s) if p.strip()]
    if parts:
        # if first part looks like an author list (contains comma or 'and'), use it
        if re.search(r"[A-Za-z]+,\s*[A-Z]", parts[0]) or re.search(r"\band\b", parts[0], re.I):
            parsed["authors"] = parts[0]
            if len(parts) >= 2:
                parsed["title"] = parts[1]
            if len(parts) >= 3:
                parsed["source"] = " ".join(parts[2:])
        else:
            parsed["title"] = parts[0]
            if len(parts) >= 2:
                parsed["source"] = " ".join(parts[1:])
    # strip whitespace
    parsed = {k: (v.strip() if isinstance(v, str) else v) for k, v in parsed.items()}
    return parsed

def check_reference_for_leeds_harvard(parsed):
    """
    Return list of suggestions (strings) telling student what to fix.
    """
    suggestions = []
    if not parsed.get("authors"):
        suggestions.append("Add author(s): Leeds Harvard starts with surname, initials (e.g. Smith, J.).")
    if not parsed.get("year"):
        suggestions.append("Add year (4-digit). Use 'n.d.' if no date is available.")
    else:
        if not re.match(r"^(19|20)\d{2}$", parsed.get("year")):
            suggestions.append("Year looks unusual; ensure it is a 4-digit year (e.g. 2023).")
    if not parsed.get("title"):
        suggestions.append("Add the title. Titles are italicised in the reference list.")
    if parsed.get("url"):
        suggestions.append("For websites include organisation/site name and an access date (e.g. Accessed: 01 January 2025).")
    else:
        if not parsed.get("source"):
            suggestions.append("Add place and publisher for books (e.g. London: Routledge) or journal details for articles.")
    return suggestions

def add_reference_to_session(parsed):
    raw = (parsed.get("raw") or "").strip()
    # avoid duplicates
    for r in st.session_state.references:
        if (r.get("raw") or "").strip().lower() == raw.lower():
            st.warning("This reference already appears in the list.")
            return False
    st.session_state.references.append(parsed)
    st.session_state.references.sort(key=surname_key)
    return True

def extract_text_from_docx_file(uploaded_file):
    try:
        uploaded_file.seek(0)
        from docx import Document
        tmp_doc = DocxDocument(uploaded_file)
        paragraphs = [p.text for p in tmp_doc.paragraphs if p.text and p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        return f"[Error reading DOCX: {e}]"

def extract_text_from_pdf_file(uploaded_file):
    try:
        uploaded_file.seek(0)
        import fitz
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = []
        for page in doc:
            text.append(page.get_text())
        return "\n".join(text)
    except Exception as e:
        return f"[Error reading PDF: {e}]"

def find_reference_section(text):
    if not text:
        return []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    idx = None
    for i, ln in enumerate(lines):
        if re.match(r"^(references|reference list|bibliography)\b", ln, re.I):
            idx = i + 1
            break
    if idx is None:
        return []
    ref_lines = []
    for ln in lines[idx:]:
        if len(ln) < 60 and ln.isupper() and not re.search(r"\d", ln):
            break
        ref_lines.append(ln)
    return ref_lines

# add_hyperlink helper (python-docx)
def add_hyperlink(paragraph, url, text, color="0000FF", underline=True):
    """
    Add a hyperlink to a python-docx paragraph. Returns the rId.
    """
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

def generate_docx_reference_list(refs, accessed_date):
    """
    Build a .docx bytes buffer containing an alphabetised reference list with titles italicised
    and URLs as active links where present. Learner supplies accessed_date string.
    """
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

        # Authors + Year
        if authors or year:
            p.add_run(f"{authors} {year}. " if year and "(" not in year else f"{authors} ({year}). ")

        # Title (italic)
        if title:
            run = p.add_run(f"{title}. ")
            run.italic = True

        # Source
        if source:
            p.add_run(f"{source}. ")

        # Available at: url (Accessed: date).
        if url:
            p.add_run("Available at: ")
            add_hyperlink(p, url, url)
            if accessed_date:
                p.add_run(f" (Accessed: {accessed_date}).")

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def scan_document_for_citations_and_mismatch(text, references):
    """
    Find in-text citations (simple heuristics) and compare with reference surnames.
    """
    if not text:
        return {}
    found = set()
    for m in re.finditer(r"\(([^(),\d]+?),\s*(19|20)\d{2}\)", text):
        surname = m.group(1).strip().split()[-1]
        found.add(surname.lower())
    for m in re.finditer(r"\b([A-Z][a-zA-Z-]+)\s*\((19|20)\d{2}\)", text):
        surname = m.group(1).strip()
        found.add(surname.lower())

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

# -----------------------------
# UI layout: sidebar input modes + main columns
# -----------------------------
with st.sidebar:
    st.header("Input & Reference Tools")
    mode = st.radio("Input mode:", (
        "Paste text",
        "Upload document",
        "URL (webpage)",
        "Manual — Book",
        "Manual — Journal article",
        "Manual — Report / Organisation",
        "Manual — Other (free-form)"
    ))
    st.markdown("---")
    st.subheader("Reference List Actions")
    if st.button("Save references (JSON)"):
        js = json.dumps(st.session_state.references, indent=2)
        st.download_button("Download JSON", data=js, file_name="references.json", mime="application/json")
    if st.button("Export Reference List (.docx)"):
        if not st.session_state.references:
            st.warning("Reference list is empty.")
        else:
            accessed_date = st.text_input("Enter Accessed date (e.g. 24 September 2025)", key="accessed_date_for_export")
            if not accessed_date:
                st.warning("Enter an access date to include in the exported references (for web links).")
            else:
                docx_buf = generate_docx_reference_list(st.session_state.references, accessed_date)
                st.download_button("Download Reference List (.docx)", data=docx_buf.getvalue(),
                                   file_name="Reference_List.docx",
                                   mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    if st.button("Clear references"):
        st.session_state.references = []
        st.success("Cleared reference list.")

# Main content area
left_col, right_col = st.columns([2, 3])

with left_col:
    st.subheader("Input & Checks")
    if mode == "Paste text":
        user_text = st.text_area("Paste the student's main text here (or sample paragraph):", height=250)
        pasted_refs = st.text_area("Paste the reference list here (one per line):", height=200)
        if st.button("Parse pasted references"):
            lines = [l.strip() for l in pasted_refs.splitlines() if l.strip()]
            count = 0
            for ln in lines:
                parsed = parse_reference_string(ln)
                add_reference_to_session(parsed)
                count += 1
            st.success(f"Parsed and added {count} references.")

    elif mode == "Upload document":
        upload_file = st.file_uploader("Upload a student's assessment (.docx or .pdf)", type=["docx", "pdf"])
        if upload_file:
            st.info("Extracting text (may take a few seconds)...")
            if upload_file.type == "application/pdf":
                txt = extract_text_from_pdf_file(upload_file)
            else:
                txt = extract_text_from_docx_file(upload_file)
            st.markdown("**Preview (first 800 chars)**")
            st.text(textwrap.shorten(txt, width=800, placeholder="..."))
            refs_found = find_reference_section(txt)
            if refs_found:
                st.markdown("**Detected reference lines:**")
                for ln in refs_found[:30]:
                    st.write(ln)
                if st.button("Parse and add detected references"):
                    for ln in refs_found:
                        parsed = parse_reference_string(ln)
                        add_reference_to_session(parsed)
                    st.success(f"Added {len(refs_found)} references from the document.")
            else:
                st.warning("No automatic References heading detected. Paste the reference list into the 'Paste text' mode or use the box below.")
                pasted = st.text_area("Or paste detected reference list here (one per line):", height=200)
                if st.button("Parse pasted list"):
                    lines = [l.strip() for l in pasted.splitlines() if l.strip()]
                    for ln in lines:
                        parsed = parse_reference_string(ln)
                        add_reference_to_session(parsed)
                    st.success(f"Parsed & added {len(lines)} references.")

    elif mode == "URL (webpage)":
        url_input = st.text_input("Enter a full webpage URL (https://...):")
        if st.button("Fetch & suggest reference"):
            if not url_input:
                st.warning("Please enter a URL.")
            else:
                try:
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
                    suggestions = check_reference_for_leeds_harvard(parsed)
                    if suggestions:
                        st.markdown("**Suggested amendments:**")
                        for sgg in suggestions:
                            st.info(sgg)
                    else:
                        st.success("This looks well-formed.")
                    if st.button("Add webpage reference to list"):
                        add_reference_to_session(parsed)
                        st.success("Added webpage reference.")
                except Exception as e:
                    st.error(f"Error fetching URL: {e}")

    elif mode == "Manual — Book":
        st.markdown("**Add a book reference (Leeds Harvard)**")
        authors = st.text_input("Author(s) (Surname, Initials):", placeholder="Smith, J.")
        year = st.text_input("Year (e.g. 2023):")
        title = st.text_input("Title (book):")
        place = st.text_input("Place of publication (e.g. London):")
        publisher = st.text_input("Publisher (e.g. Routledge):")
        url = st.text_input("URL (optional):")
        if st.button("Generate book reference"):
            source = f"{place}: {publisher}" if place and publisher else publisher or place
            raw = f"{authors} {year}. {title}. {source}."
            if url:
                raw = raw + f" {url}"
            parsed = {"raw": raw, "authors": authors, "year": year, "title": title, "source": source, "url": url}
            suggestions = check_reference_for_leeds_harvard(parsed)
            if suggestions:
                st.markdown("**Suggested amendments:**")
                for sgg in suggestions:
                    st.info(sgg)
            added = add_reference_to_session(parsed)
            if added:
                st.success("Book reference added to Reference List.")

    elif mode == "Manual — Journal article":
        st.markdown("**Add a journal article reference (Leeds Harvard)**")
        authors = st.text_input("Author(s) (Surname, Initials):", placeholder="Smith, J.")
        year = st.text_input("Year:")
        article_title = st.text_input("Article title:")
        journal = st.text_input("Journal title:")
        volume = st.text_input("Volume:")
        issue = st.text_input("Issue (no.):")
        pages = st.text_input("Page numbers (e.g. 12-28):")
        doi = st.text_input("DOI or URL (optional):")
        if st.button("Generate journal reference"):
            source_parts = [journal]
            if volume:
                source_parts.append(volume)
            if issue:
                source_parts.append(f"({issue})")
            if pages:
                source_parts.append(f"pp. {pages}")
            source = " ".join([p for p in source_parts if p])
            raw = f"{authors} {year}. {article_title}. {source}."
            if doi:
                raw = raw + f" {doi}"
            parsed = {"raw": raw, "authors": authors, "year": year, "title": article_title, "source": source, "url": doi}
            suggestions = check_reference_for_leeds_harvard(parsed)
            if suggestions:
                st.markdown("**Suggested amendments:**")
                for sgg in suggestions:
                    st.info(sgg)
            added = add_reference_to_session(parsed)
            if added:
                st.success("Journal article added to Reference List.")

    elif mode == "Manual — Report / Organisation":
        st.markdown("**Add a report / organisational source**")
        organisation = st.text_input("Organisation (as author):", placeholder="World Health Organization")
        year = st.text_input("Year:")
        title = st.text_input("Title:")
        publisher = st.text_input("Publisher (if different):")
        url = st.text_input("URL (optional):")
        if st.button("Generate report reference"):
            authors = organisation
            source = publisher or organisation
            raw = f"{authors} {year}. {title}. {source}."
            if url:
                raw = raw + f" {url}"
            parsed = {"raw": raw, "authors": authors, "year": year, "title": title, "source": source, "url": url}
            suggestions = check_reference_for_leeds_harvard(parsed)
            if suggestions:
                st.markdown("**Suggested amendments:**")
                for sgg in suggestions:
                    st.info(sgg)
            added = add_reference_to_session(parsed)
            if added:
                st.success("Report/organisation reference added.")

    elif mode == "Manual — Other (free-form)":
        raw = st.text_area("Paste or type the reference (free-form):", height=140)
        if st.button("Analyse & add free-form reference"):
            parsed = parse_reference_string(raw)
            st.json(parsed)
            suggestions = check_reference_for_leeds_harvard(parsed)
            if suggestions:
                st.markdown("**Suggested amendments:**")
                for sgg in suggestions:
                    st.info(sgg)
            added = add_reference_to_session(parsed)
            if added:
                st.success("Free-form reference added.")

with right_col:
    st.subheader("Reference List (Leeds Harvard)")
    st.markdown("References are shown alphabetically by author surname. Titles are italicised.")
    st.markdown("---")
    if st.session_state.references:
        for r in sorted(st.session_state.references, key=surname_key):
            st.markdown(format_display_reference(r), unsafe_allow_html=True)
    else:
        st.info("Reference list is empty. Add references from the left-hand panel.")

    st.markdown("---")
    st.subheader("Checks on uploaded assessment")
    st.write("optional: upload the same assessment to check cited surnames vs reference list")
    check_file = st.file_uploader("Upload assessment to check", type=["docx", "pdf"], key="check_file")
    if check_file is not None:
        if check_file.type == "application/pdf":
            full_text = extract_text_from_pdf_file(check_file)
        else:
            full_text = extract_text_from_docx_file(check_file)
        st.write("Analyzing document...")
        results = scan_document_for_citations_and_mismatch(full_text, st.session_state.references)
        if not results:
            st.info("No textual content could be extracted.")
        else:
            st.markdown("**In-text citations detected (sample):**")
            st.write(results.get("found_citations", []))
            if results.get("missing_in_refs"):
                st.error("Citations in text that are NOT present in the reference list:")
                for s in results["missing_in_refs"]:
                    st.write(f"- {s} — student should add a full Leeds Harvard reference.")
            else:
                st.success("All detected surnames appear in the reference list.")
            if results.get("not_cited_in_text"):
                st.warning("References present in list but not found as in-text citations:")
                for s in results["not_cited_in_text"]:
                    st.write(f"- {s} — check whether this reference was used.")

# Footer (fixed)
st.markdown(
    """
    <div class="footer">
        <img src="assets/logo-circle.png" alt="Logo">
        © 2025 <a href="https://macmillancentreforlearning.co.uk" target="_blank">Macmillan Centre for Learning</a>
    </div>
    """,
    unsafe_allow_html=True
)
