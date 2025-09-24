# streamlit_leeds_harvard_tool.py
"""
Leeds Harvard Referencing Tool - Streamlit app
Full tool: header + sidebar input modes + parsing + suggestions + exports (DOCX/PDF/XLSX/TXT)
"""

import re
import json
import requests
import textwrap
from io import BytesIO
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path

import streamlit as st
from bs4 import BeautifulSoup
from docx import Document as DocxDocument
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from PyPDF2 import PdfReader
import openpyxl
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# -----------------------------
# Page config + CSS (brand colours)
# -----------------------------
st.set_page_config(page_title="Leeds Harvard Referencing Tool",
                   page_icon="📚",
                   layout="wide")

st.markdown(
    f"""
    <style>
        :root {{
            --bg: #e6f7f8;             /* Background */
            --header-bg: #00a2b3;      /* Header Background */
            --header-text: #ffffff;    /* Header Text */
            --muted-text: #37474f;     /* Text */
            --border: #80cbc4;
            --link: #0288d1;
            --footer-bg: #00a2b3;
        }}
        body {{
            background-color: var(--bg);
            color: var(--muted-text);
        }}
        .header-row {{
            display:flex;
            align-items:center;
            gap:18px;
            margin-bottom: 12px;
        }}
        .header-row img.header-banner {{
            width:100%;
            max-height:110px;
            object-fit:contain;
            border-radius:8px;
        }}
        .logo-small {{
            height:56px;
            width:56px;
            border-radius:50%;
            object-fit:cover;
        }}
        .tool-title {{
            color: var(--header-bg);
            margin:0;
            padding:0;
            font-size:28px;
            line-height:1.05;
        }}
        .tool-sub {{
            margin:0;
            font-size:14px;
            color:#5f6b6b;
        }}
        .ref-box {{
            background: white;
            border: 1px solid var(--border);
            padding: 12px;
            border-radius: 8px;
        }}
        .footer {{
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: var(--footer-bg);
            color: white;
            text-align: center;
            padding: 10px;
            font-size: 14px;
            z-index: 100;
        }}
        .footer img {{
            height: 20px;
            vertical-align: middle;
            margin-right: 8px;
        }}
        a {{ color: var(--link); }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Header (banner + small logo + title)
# -----------------------------
# show header banner full width (use image in assets/Header.png)
header_banner_path = "assets/Header.png"
logo_small_path = "assets/logo-circle.png"

# If banner exists, display it; otherwise show title row
if Path(header_banner_path).exists():
    st.image(header_banner_path, use_column_width=True, caption=None)
else:
    # fallback: show logo + title row
    col_logo, col_title = st.columns([1, 6])
    with col_logo:
        if Path(logo_small_path).exists():
            st.image(logo_small_path, caption=None, width=72)
    with col_title:
        st.markdown("<h1 class='tool-title'>Leeds Harvard Referencing Tool</h1>", unsafe_allow_html=True)
        st.markdown("<div class='tool-sub'>Macmillan Centre for Learning — guidance and checks to help students learn Leeds Harvard referencing (not an automatic fixer)</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div style="margin-top:6px; margin-bottom:8px;">
    <strong>Leeds Harvard Referencing Checker & Guide</strong> — identifies missing components for Leeds Harvard referencing and explains what students should change.
    &nbsp;|&nbsp;<a href="https://library.leeds.ac.uk/info/1404/referencing/46/harvard_style" target="_blank" rel="noopener">Leeds Harvard guidance</a>
    &nbsp;|&nbsp;<a href="https://macmillancentreforlearning.co.uk" target="_blank" rel="noopener">Macmillan Centre for Learning</a>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# Session state: references list
# -----------------------------
if "references" not in st.session_state:
    # references stored as list of dicts: {authors, year, title, source, url, raw, accessed}
    st.session_state.references = []

# -----------------------------
# Helper functions
# -----------------------------
def surname_key(ref):
    """Return primary sorting key (surname of first author) for alphabetical ordering."""
    authors = (ref.get("authors") or "").strip()
    if "," in authors:
        return authors.split(",")[0].strip().lower()
    else:
        return (authors.split()[0].strip().lower() if authors else "")

def format_display_reference_html(ref):
    """Return HTML safe formatted reference for display (title italicised)."""
    authors = (ref.get("authors") or "").strip()
    year = (ref.get("year") or "").strip()
    title = (ref.get("title") or "").strip()
    source = (ref.get("source") or "").strip()
    url = (ref.get("url") or "").strip()

    header = ""
    if authors:
        header += f"{authors}"
    if year:
        header += (f" ({year})")
    if header:
        header += ". "

    title_html = f"<em>{title}</em>" if title else ""
    remainder = ""
    if source:
        remainder = f" {source}."
    if url:
        remainder += f' <a href="{url}" target="_blank" rel="noopener">{url}</a>'

    return f"{header}{title_html}{remainder}"

def parse_reference_string(s):
    """
    Heuristic parser for a free-text reference line -> dict keys authors, year, title, source, url, raw.
    """
    s = (s or "").strip()
    parsed = {"raw": s, "authors": "", "year": "", "title": "", "source": "", "url": "", "accessed": ""}
    if not s:
        return parsed

    # extract URL if present (first http...)
    url_match = re.search(r"(https?://\S+)", s)
    if url_match:
        parsed["url"] = url_match.group(1).rstrip(".,)")
        s = s.replace(url_match.group(1), "").strip()

    # extract year like 2023 or 1999
    year_match = re.search(r"\b(19|20)\d{2}\b", s)
    if year_match:
        parsed["year"] = year_match.group(0)
        s = s.replace(year_match.group(0), "").strip(" .,")

    # split into parts by full stop
    parts = [p.strip() for p in re.split(r"\.\s+", s) if p.strip()]
    if parts:
        # heuristics: if first part has comma or 'and' it's likely authors
        if re.search(r"[A-Za-z]+,\s*[A-Z]", parts[0]) or re.search(r"\band\b", parts[0], re.I):
            parsed["authors"] = parts[0]
            if len(parts) >= 2:
                parsed["title"] = parts[1]
            if len(parts) >= 3:
                parsed["source"] = " ".join(parts[2:])
        else:
            # first part may be title
            parsed["title"] = parts[0]
            if len(parts) >= 2:
                parsed["source"] = " ".join(parts[1:])
    # final cleanup
    for k in parsed:
        if isinstance(parsed[k], str):
            parsed[k] = parsed[k].strip()
    return parsed

def check_reference_for_leeds_harvard(parsed):
    """
    Return list of suggestions for student (no auto-fixing).
    """
    suggestions = []
    if not parsed.get("authors"):
        suggestions.append("Add author(s): Leeds Harvard starts with surname then initials (e.g. Smith, J.).")
    if not parsed.get("year"):
        suggestions.append("Add year (4-digit). Use 'n.d.' if no date is available.")
    else:
        if not re.match(r"^(19|20)\d{2}$", parsed.get("year")):
            suggestions.append("Year looks unusual; use a 4-digit year (e.g. 2023).")
    if not parsed.get("title"):
        suggestions.append("Add the title (the title is italicised in the reference list).")
    if parsed.get("url"):
        suggestions.append("For websites include the organisation/site name and an Accessed date (e.g. Accessed: 24 September 2025).")
    else:
        if not parsed.get("source"):
            suggestions.append("Add place & publisher for books (e.g. London: Routledge), or journal title/volume for articles.")
    return suggestions

def add_reference(parsed):
    """Append parsed reference dict to session_state if not duplicate; returns True if added."""
    raw = (parsed.get("raw") or "").strip()
    for r in st.session_state.references:
        if (r.get("raw") or "").strip().lower() == raw.lower() and raw != "":
            st.warning("This reference already exists in the list.")
            return False
    st.session_state.references.append(parsed)
    st.session_state.references.sort(key=surname_key)
    return True

# python-docx helper to add hyperlink
def add_hyperlink(paragraph, url, text, color="0000FF", underline=True):
    """
    Add a hyperlink to a python-docx paragraph.
    Returns the relationship id.
    """
    part = paragraph.part
    r_id = part.relate_to(url, RT.HYPERLINK, is_external=True)

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")

    if color:
        c = OxmlElement("w:color")
        c.set(qn("w:val"), color)
        rPr.append(c)
    if underline:
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rPr.append(u)

    new_run.append(rPr)
    t = OxmlElement("w:t")
    t.text = text
    new_run.append(t)

    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)

    return r_id

def generate_docx_reference_list(refs, accessed_date=""):
    """
    Create a .docx bytes buffer containing an alphabetised reference list.
    Titles italicised; URLs inserted as live hyperlinks with 'Available at: URL (Accessed: date)'.
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
        header_text = ""
        if authors:
            header_text += authors
        if year:
            # display year in parentheses
            header_text += f" ({year})"
        if header_text:
            run = p.add_run(header_text + ". ")

        # Title (italic)
        if title:
            run = p.add_run(title + ". ")
            run.italic = True

        # Source
        if source:
            p.add_run(source + ". ")

        # URL
        if url:
            p.add_run("Available at: ")
            add_hyperlink(p, url, url)
            # Accessed: prefer per-ref accessed if present, else global accessed_date
            ref_accessed = r.get("accessed") or accessed_date or ""
            if ref_accessed:
                p.add_run(f" (Accessed: {ref_accessed}).")
            else:
                p.add_run(".")

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

def export_as_pdf(references, accessed_date=""):
    """
    Export simple PDF with heading + references (no live links — PDF hyperlinks are more work).
    """
    bio = BytesIO()
    doc = SimpleDocTemplate(bio)
    styles = getSampleStyleSheet()
    elements = [Paragraph("Reference List", styles["Heading1"]), Spacer(1, 8)]
    for r in sorted(references, key=surname_key):
        # format as simple text (title italic in PDF is optional; we'll keep plain)
        authors = r.get("authors", "")
        year = r.get("year", "")
        title = r.get("title", "")
        source = r.get("source", "")
        url = r.get("url", "")
        ref_text = ""
        if authors:
            ref_text += authors
        if year:
            ref_text += f" ({year})"
        if title:
            ref_text += f" {title}."
        if source:
            ref_text += f" {source}."
        if url:
            ref_accessed = r.get("accessed") or accessed_date or ""
            ref_text += f" Available at: {url}"
            if ref_accessed:
                ref_text += f" (Accessed: {ref_accessed})."
        elements.append(Paragraph(ref_text, styles["Normal"]))
        elements.append(Spacer(1, 6))
    doc.build(elements)
    bio.seek(0)
    return bio

def export_as_xlsx(references, accessed_date=""):
    """
    Export references to an Excel workbook (simple sheet with columns).
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "References"
    ws.append(["Authors", "Year", "Title", "Source", "URL", "Accessed", "Raw"])
    for r in sorted(references, key=surname_key):
        accessed = r.get("accessed") or accessed_date or ""
        ws.append([r.get("authors",""), r.get("year",""), r.get("title",""), r.get("source",""), r.get("url",""), accessed, r.get("raw","")])
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio

def export_as_txt(references, accessed_date=""):
    lines = []
    for r in sorted(references, key=surname_key):
        accessed = r.get("accessed") or accessed_date or ""
        line = r.get("raw") or ""
        if r.get("url"):
            if accessed:
                line = f"{line} Available at: {r.get('url')} (Accessed: {accessed})."
            else:
                line = f"{line} {r.get('url')}"
        lines.append(line)
    return BytesIO("\n".join(lines).encode("utf-8"))

# -----------------------------
# UI layout: sidebar + main columns
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
        "Manual — Other"
    ))
    st.markdown("---")
    st.subheader("Reference list actions")
    if st.button("Save references (JSON)"):
        js = json.dumps(st.session_state.references, indent=2)
        st.download_button("Download JSON", data=js, file_name="references.json", mime="application/json")
    st.markdown("**Export reference list**")
    accessed_date_global = st.text_input("Enter access date for web links (free text)", help="Students should enter the date they accessed the web resource, e.g. 24 September 2025")
    if st.button("Export as DOCX"):
        if not st.session_state.references:
            st.warning("Reference list is empty.")
        else:
            docx_buf = generate_docx_reference_list(st.session_state.references, accessed_date_global)
            st.download_button("Download Reference List (.docx)", data=docx_buf.getvalue(),
                               file_name="Reference_List.docx",
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    if st.button("Export as PDF"):
        if not st.session_state.references:
            st.warning("Reference list is empty.")
        else:
            pdf_buf = export_as_pdf(st.session_state.references, accessed_date_global)
            st.download_button("Download Reference List (.pdf)", data=pdf_buf.getvalue(), file_name="Reference_List.pdf", mime="application/pdf")
    if st.button("Export as Excel (XLSX)"):
        if not st.session_state.references:
            st.warning("Reference list is empty.")
        else:
            xlsx_buf = export_as_xlsx(st.session_state.references, accessed_date_global)
            st.download_button("Download Reference List (.xlsx)", data=xlsx_buf.getvalue(), file_name="Reference_List.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if st.button("Export as TXT"):
        if not st.session_state.references:
            st.warning("Reference list is empty.")
        else:
            txt_buf = export_as_txt(st.session_state.references, accessed_date_global)
            st.download_button("Download Reference List (.txt)", data=txt_buf.getvalue(), file_name="Reference_List.txt", mime="text/plain")
    if st.button("Clear references"):
        st.session_state.references = []
        st.success("Reference list cleared.")

# Main columns
left_col, right_col = st.columns([2, 3])

with left_col:
    st.subheader("Input & Add References")

    if mode == "Paste text":
        text_area = st.text_area("Paste student text or reference list here (one ref per line):", height=240)
        if st.button("Parse pasted reference lines"):
            lines = [l.strip() for l in text_area.splitlines() if l.strip()]
            if not lines:
                st.warning("No lines found.")
            else:
                added = 0
                for ln in lines:
                    parsed = parse_reference_string(ln)
                    if add_reference(parsed):
                        added += 1
                st.success(f"Added {added} references from pasted text.")

    elif mode == "Upload document":
        upload_file = st.file_uploader("Upload .docx or .pdf (will try to extract reference section)", type=["docx", "pdf"])
        if upload_file is not None:
            st.info("Extracting text (may take a few seconds)...")
            if upload_file.type == "application/pdf":
                txt = ""
                try:
                    txt = extract_text_from_pdf(upload_file)
                except Exception as e:
                    txt = f"[Error reading PDF: {e}]"
            else:
                txt = ""
                try:
                    txt = extract_text_from_docx(upload_file)
                except Exception as e:
                    txt = f"[Error reading DOCX: {e}]"
            st.markdown("**Preview (first 800 chars)**")
            st.text(textwrap.shorten(txt, width=800, placeholder="..."))
            detected = find_reference_section(txt)
            if detected:
                st.markdown("**Detected reference lines (example first 30)**")
                for ln in detected[:30]:
                    st.write(ln)
                if st.button("Parse detected references and add"):
                    count = 0
                    for ln in detected:
                        parsed = parse_reference_string(ln)
                        if add_reference(parsed):
                            count += 1
                    st.success(f"Added {count} references from document.")
            else:
                st.warning("No 'References' heading automatically detected. You can paste the reference list into the 'Paste text' mode or paste below.")
                pasted = st.text_area("Or paste the reference list here (one per line):", height=160)
                if st.button("Parse pasted list"):
                    lines = [l.strip() for l in pasted.splitlines() if l.strip()]
                    c = 0
                    for ln in lines:
                        parsed = parse_reference_string(ln)
                        if add_reference(parsed):
                            c += 1
                    st.success(f"Added {c} references from pasted list.")

    elif mode == "URL (webpage)":
        url_input = st.text_input("Enter the full webpage URL (https://...)")
        if st.button("Fetch & suggest web reference"):
            if not url_input.strip():
                st.warning("Enter a URL.")
            else:
                try:
                    r = requests.get(url_input, timeout=8)
                    s = BeautifulSoup(r.text, "html.parser")
                    title = s.title.string.strip() if s.title and s.title.string else ""
                    site = urlparse(url_input).netloc
                    raw = f"{site} (n.d.) {title}. {url_input}"
                    parsed = {"raw": raw, "authors": site, "year": "n.d.", "title": title, "source": site, "url": url_input, "accessed": ""}
                    st.json(parsed)
                    suggestions = check_reference_for_leeds_harvard(parsed)
                    if suggestions:
                        st.markdown("**Suggested amendments:**")
                        for sgg in suggestions:
                            st.info(sgg)
                    if st.button("Add webpage reference to list"):
                        if add_reference(parsed):
                            st.success("Webpage reference added to Reference List.")
                except Exception as e:
                    st.error(f"Error fetching URL: {e}")

    elif mode == "Manual — Book":
        st.markdown("**Add a book (Leeds Harvard)**")
        m_authors = st.text_input("Author(s) (Surname, Initials):", placeholder="Smith, J.")
        m_year = st.text_input("Year (e.g. 2023):")
        m_title = st.text_input("Title (book):")
        m_edition = st.text_input("Edition (optional):")
        m_place = st.text_input("Place of publication (e.g. London):")
        m_publisher = st.text_input("Publisher (e.g. Routledge):")
        m_url = st.text_input("URL (optional):")
        m_accessed = st.text_input("Accessed date (optional) — free text (e.g. 24 September 2025)")
        if st.button("Add book reference"):
            source = f"{m_place}: {m_publisher}" if m_place and m_publisher else m_publisher or m_place
            raw = f"{m_authors} {m_year}. {m_title}. {source}."
            if m_url:
                raw = raw + f" {m_url}"
            parsed = {"raw": raw, "authors": m_authors, "year": m_year, "title": m_title, "source": source, "url": m_url or "", "accessed": m_accessed or ""}
            suggestions = check_reference_for_leeds_harvard(parsed)
            if suggestions:
                st.markdown("**Suggested amendments:**")
                for sgg in suggestions:
                    st.info(sgg)
            if add_reference(parsed):
                st.success("Book reference added to Reference List.")

    elif mode == "Manual — Journal article":
        st.markdown("**Add a journal article (Leeds Harvard)**")
        j_authors = st.text_input("Author(s) (Surname, Initials):", key="j_authors")
        j_year = st.text_input("Year:", key="j_year")
        j_title = st.text_input("Article title:", key="j_title")
        j_journal = st.text_input("Journal title:", key="j_journal")
        j_volume = st.text_input("Volume:", key="j_volume")
        j_issue = st.text_input("Issue (no.):", key="j_issue")
        j_pages = st.text_input("Page numbers (e.g. 12-28):", key="j_pages")
        j_doi = st.text_input("DOI or URL (optional):", key="j_doi")
        j_accessed = st.text_input("Accessed date (optional)", key="j_accessed")
        if st.button("Add journal article"):
            source_parts = []
            if j_journal:
                source_parts.append(j_journal)
            if j_volume:
                source_parts.append(j_volume)
            if j_issue:
                source_parts.append(f"({j_issue})")
            if j_pages:
                source_parts.append(f"pp. {j_pages}")
            source = " ".join(source_parts)
            raw = f"{j_authors} {j_year}. {j_title}. {source}."
            if j_doi:
                raw = raw + f" {j_doi}"
            parsed = {"raw": raw, "authors": j_authors, "year": j_year, "title": j_title, "source": source, "url": j_doi or "", "accessed": j_accessed or ""}
            suggestions = check_reference_for_leeds_harvard(parsed)
            if suggestions:
                st.markdown("**Suggested amendments:**")
                for sgg in suggestions:
                    st.info(sgg)
            if add_reference(parsed):
                st.success("Journal article added to Reference List.")

    elif mode == "Manual — Report / Organisation":
        st.markdown("**Add a report / organisational source**")
        r_org = st.text_input("Organisation (as author):", key="r_org")
        r_year = st.text_input("Year:", key="r_year")
        r_title = st.text_input("Title:", key="r_title")
        r_publisher = st.text_input("Publisher (if different):", key="r_publisher")
        r_url = st.text_input("URL (optional):", key="r_url")
        r_accessed = st.text_input("Accessed date (optional):", key="r_accessed")
        if st.button("Add report reference"):
            authors = r_org
            source = r_publisher or r_org
            raw = f"{authors} {r_year}. {r_title}. {source}."
            if r_url:
                raw = raw + f" {r_url}"
            parsed = {"raw": raw, "authors": authors, "year": r_year, "title": r_title, "source": source, "url": r_url or "", "accessed": r_accessed or ""}
            suggestions = check_reference_for_leeds_harvard(parsed)
            if suggestions:
                st.markdown("**Suggested amendments:**")
                for sgg in suggestions:
                    st.info(sgg)
            if add_reference(parsed):
                st.success("Report reference added to Reference List.")

    elif mode == "Manual — Other":
        st.markdown("**Add other reference (free form)**")
        o_author = st.text_input("Author/Organisation", key="o_author")
        o_year = st.text_input("Year", key="o_year")
        o_title = st.text_input("Title/Description", key="o_title")
        o_publisher = st.text_input("Publisher / Source", key="o_publisher")
        o_url = st.text_input("URL (optional)", key="o_url")
        o_accessed = st.text_input("Accessed date (optional)", key="o_accessed")
        if st.button("Add other reference"):
            raw = f"{o_author} {o_year}. {o_title}. {o_publisher}."
            if o_url:
                raw = raw + f" {o_url}"
            parsed = {"raw": raw, "authors": o_author, "year": o_year, "title": o_title, "source": o_publisher, "url": o_url or "", "accessed": o_accessed or ""}
            suggestions = check_reference_for_leeds_harvard(parsed)
            if suggestions:
                st.markdown("**Suggested amendments:**")
                for sgg in suggestions:
                    st.info(sgg)
            if add_reference(parsed):
                st.success("Reference added to Reference List.")

with right_col:
    st.subheader("Reference List (Leeds Harvard)")
    st.markdown("References are shown alphabetically by author surname. Titles are italicised where present.")
    st.markdown("---")
    if st.session_state.references:
        for r in sorted(st.session_state.references, key=surname_key):
            st.markdown(format_display_reference_html(r), unsafe_allow_html=True)
    else:
        st.info("Reference list is empty. Add parsed references from the left-hand panel.")

    st.markdown("---")
    st.subheader("Citation vs Reference checks (optional)")
    st.write("Upload the assessment DOCX or PDF to run a quick check of cited surnames vs reference list.")
    check_file = st.file_uploader("Upload assessment to check", type=["docx", "pdf"], key="check_file")
    if check_file is not None:
        if check_file.type == "application/pdf":
            full_text = extract_text_from_pdf(check_file)
        else:
            full_text = extract_text_from_docx(check_file)
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

# -----------------------------
# Small footer and credits (fixed)
# -----------------------------
st.markdown(
    f"""
    <div class="footer">
        <img src="{logo_small_path}" alt="Logo">
        © {datetime.now().year} <a href="https://macmillancentreforlearning.co.uk" target="_blank" rel="noopener">Macmillan Centre for Learning</a>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# End of file
# -----------------------------
