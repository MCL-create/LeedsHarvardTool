# streamlit_leeds_harvard_tool.py
"""
Final production-ready Leeds Harvard Referencing Tool
Includes:
 - Header + footer + navigation
 - Upload/paste/URL/manual input
 - Heuristic parsing + inline Leeds Harvard fix suggestions
 - Citation vs reference checks
 - Exports: DOCX, XLSX, PDF, TXT
 - Robust text extraction for DOCX/PDF (tries multiple libraries)
 - Branding/colors per brief
"""

import os
# Ensure Render-provided PORT is respected if present
if os.environ.get("PORT"):
    os.environ["STREAMLIT_SERVER_PORT"] = os.environ.get("PORT")

import re
import json
import textwrap
from io import BytesIO
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st
import requests
from bs4 import BeautifulSoup

# docx / pdf libs
from docx import Document as DocxDocument
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

# Try to import optional robust extraction libraries
try:
    import docx2txt
except Exception:
    docx2txt = None

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

import openpyxl
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# ---------------------------
# App config + CSS (branding)
# ---------------------------
st.set_page_config(page_title="Leeds Harvard Referencing Tool",
                   page_icon="📚",
                   layout="wide")

# Branding colours (from your brief)
BG = "#e6f7f8"
HEADER_BG = "#00a2b3"
HEADER_TEXT = "#ffffff"
BUTTON_BG = "#009688"
ACCENT_WARM = "#f9a825"
ACCENT_COOL = "#5c6bc0"
MUTED_TEXT = "#37474f"
BORDER = "#80cbc4"
HOVER = "#00796b"
SECONDARY_BG = "#f1f8e9"
HIGHLIGHT = "#ffccbc"
LINK = "#0288d1"

st.markdown(
    f"""
    <style>
      :root {{
        --bg: {BG};
        --header-bg: {HEADER_BG};
        --header-text: {HEADER_TEXT};
        --muted-text: {MUTED_TEXT};
        --border: {BORDER};
        --link: {LINK};
        --footer-bg: {HEADER_BG};
        --button-bg: {BUTTON_BG};
        --accent-warm: {ACCENT_WARM};
        --accent-cool: {ACCENT_COOL};
      }}
      body {{ background-color: var(--bg); color: var(--muted-text); }}
      .header-row {{ display:flex; align-items:center; gap:18px; margin-bottom:12px; }}
      .header-banner {{ width:100%; max-height:120px; object-fit:contain; border-radius:8px; }}
      .logo-small {{ height:56px; width:56px; border-radius:50%; object-fit:cover; }}
      .tool-title {{ color: var(--header-bg); margin:0; font-size:28px; }}
      .tool-sub {{ margin:0; font-size:14px; color:#5f6b6b; }}
      .ref-box {{ background: white; border: 1px solid var(--border); padding: 12px; border-radius: 8px; }}
      .footer {{ position: fixed; left: 0; bottom: 0; width: 100%; background-color: var(--footer-bg); color: white; text-align: center; padding: 10px; font-size: 14px; z-index: 100; }}
      .footer img {{ height: 20px; vertical-align: middle; margin-right: 8px; border-radius:50%; }}
      .btn-custom {{ background-color: var(--button-bg); color: white; padding:6px 10px; border-radius:6px; }}
      a {{ color: var(--link); }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Header: banner if present, else logo+title row
# ---------------------------
HEADER_BANNER = "assets/Header.png"
LOGO_SMALL = "assets/logo-circle.png"

if Path(HEADER_BANNER).exists():
    st.image(HEADER_BANNER, use_column_width=True)
else:
    col_logo, col_title = st.columns([1, 6])
    with col_logo:
        if Path(LOGO_SMALL).exists():
            st.image(LOGO_SMALL, width=80)
    with col_title:
        st.markdown(f"<h1 class='tool-title'>Leeds Harvard Referencing Tool</h1>", unsafe_allow_html=True)
        st.markdown("<div class='tool-sub'>Macmillan Centre for Learning — guidance and checks to help students learn Leeds Harvard referencing (not an automatic fixer)</div>", unsafe_allow_html=True)

st.markdown(
    '<div style="margin-top:6px; margin-bottom:10px;"><strong>Leeds Harvard Referencing Checker & Guide</strong> — identifies missing components for Leeds Harvard referencing and explains what students should change.</div>',
    unsafe_allow_html=True
)

# ---------------------------
# Session: references store
# ---------------------------
if "references" not in st.session_state:
    st.session_state.references = []  # list of dicts: raw, authors, year, title, source, url, accessed

if "last_parsed" not in st.session_state:
    st.session_state.last_parsed = None

# ---------------------------
# Utility & helper functions
# ---------------------------
def safe_extract_text_docx(file_like):
    """Try python-docx then docx2txt if available."""
    try:
        file_like.seek(0)
        doc = DocxDocument(file_like)
        paras = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
        return "\n".join(paras)
    except Exception:
        if docx2txt:
            try:
                # docx2txt expects filename; write temp bytes
                tmp_path = Path("tmp_upload.docx")
                tmp_path.write_bytes(file_like.read())
                txt = docx2txt.process(str(tmp_path))
                tmp_path.unlink(missing_ok=True)
                return txt
            except Exception as e:
                return f"[docx2txt error: {e}]"
        return "[Error extracting DOCX]"

def safe_extract_text_pdf(file_like):
    """Try PyMuPDF (fitz) then PyPDF2."""
    try:
        if fitz:
            file_like.seek(0)
            pdf = fitz.open(stream=file_like.read(), filetype="pdf")
            texts = []
            for page in pdf:
                texts.append(page.get_text())
            return "\n".join(texts)
    except Exception:
        pass
    # fallback to PyPDF2
    try:
        if PdfReader:
            file_like.seek(0)
            reader = PdfReader(file_like)
            texts = []
            for p in reader.pages:
                t = p.extract_text()
                if t:
                    texts.append(t)
            return "\n".join(texts)
    except Exception as e:
        return f"[PDF extraction error: {e}]"
    return "[Error extracting PDF]"

def surname_key(ref):
    authors = (ref.get("authors") or "").strip()
    if "," in authors:
        return authors.split(",")[0].strip().lower()
    return (authors.split()[0].strip().lower() if authors else "")

def parse_reference_string(s):
    """Heuristic parser to break a free-text reference into fields."""
    s = (s or "").strip()
    parsed = {"raw": s, "authors": "", "year": "", "title": "", "source": "", "url": "", "accessed": ""}
    if not s:
        return parsed
    # URL
    m = re.search(r"(https?://\S+)", s)
    if m:
        parsed["url"] = m.group(1).rstrip(".,)")
        s = s.replace(m.group(1), "").strip()
    # year
    y = re.search(r"\b(19|20)\d{2}\b", s)
    if y:
        parsed["year"] = y.group(0)
        s = s.replace(y.group(0), "").strip(" .,")

    parts = [p.strip() for p in re.split(r"\.\s+", s) if p.strip()]
    if parts:
        # if first part looks like "Surname, I." or contains 'and', treat as authors
        if re.search(r"[A-Za-z]+,\s*[A-Z]", parts[0]) or re.search(r"\band\b", parts[0], re.I):
            parsed["authors"] = parts[0]
            parsed["title"] = parts[1] if len(parts) >= 2 else ""
            parsed["source"] = " ".join(parts[2:]) if len(parts) >= 3 else ""
        else:
            parsed["title"] = parts[0]
            parsed["source"] = " ".join(parts[1:]) if len(parts) >= 2 else ""
    # cleanup
    for k in parsed:
        if isinstance(parsed[k], str):
            parsed[k] = parsed[k].strip()
    return parsed

def check_reference_for_leeds_harvard(parsed):
    """Return suggestions (list) for correction (no auto-modification)."""
    suggestions = []
    if not parsed.get("authors"):
        suggestions.append("Add author(s): Leeds Harvard begins with surname then initials (e.g. Smith, J.).")
    if not parsed.get("year"):
        suggestions.append("Add year (4-digit), or use 'n.d.' if no date is available.")
    else:
        if not re.match(r"^(19|20)\d{2}$", parsed.get("year")):
            suggestions.append("Year looks unusual; ensure it's a 4-digit year (e.g. 2023).")
    if not parsed.get("title"):
        suggestions.append("Add the title. In Leeds Harvard the title is italicised in the reference list.")
    if parsed.get("url"):
        suggestions.append("For websites, include site/organisation and an accessed date (e.g. Accessed: 24 September 2025).")
    else:
        if not parsed.get("source"):
            suggestions.append("Add place & publisher for books (e.g. London: Routledge) or journal title/volume for articles.")
    return suggestions

def format_to_leeds(parsed):
    """
    Produce a suggested Leeds Harvard formatted reference string for the parsed dict.
    This is a best-effort reformat to show students how to correct their entry.
    """
    authors = parsed.get("authors","").strip()
    year = parsed.get("year","").strip() or "n.d."
    title = parsed.get("title","").strip()
    source = parsed.get("source","").strip()
    url = parsed.get("url","").strip()
    accessed = parsed.get("accessed","").strip()

    # If looks like a journal (source contains journal name and volume/page)
    if source and ("journal" in source.lower() or "pp." in source.lower() or re.search(r"\d+,\s*\d+", source)):
        # journal article style
        # Example: Smith, J. 2023. 'Title of article', Journal Title, 12(1), pp. 15-30.
        parts = []
        if authors:
            parts.append(authors)
        parts.append(year)
        header = ". ".join([p for p in parts if p]).strip() + ". "
        title_part = f"'{title}'." if title else ""
        return f"{header} {title_part} {source}{(' Available at: ' + url + (' (Accessed: ' + accessed + ')' if accessed else '')) if url else ''}".strip()

    # Website resource
    if url and not source:
        # e.g. Organisation (n.d.) Title. Available at: URL (Accessed: date).
        org = authors or urlparse(url).netloc
        return f"{org} ({year}) {title}. Available at: {url}" + (f" (Accessed: {accessed})." if accessed else "")

    # Book or generic
    # e.g. Smith, J. (2023) Title. Place: Publisher.
    if source and ":" in source:
        # assume "Place: Publisher" already
        place_pub = source
    else:
        place_pub = source
    header = f"{authors} ({year})." if authors else f"({year})."
    title_part = f" {title}." if title else ""
    src_part = f" {place_pub}." if place_pub else ""
    url_part = f" Available at: {url}" if url else ""
    accessed_part = f" (Accessed: {accessed})." if url and accessed else ("." if (url and not accessed) else "")
    return f"{header}{title_part}{src_part}{url_part}{accessed_part}".strip()

def add_reference(parsed):
    """Add parsed ref to session_state if not duplicate; return True if added."""
    raw = (parsed.get("raw") or "").strip()
    if raw:
        for r in st.session_state.references:
            if (r.get("raw") or "").strip().lower() == raw.lower():
                st.warning("That reference already exists in the list.")
                return False
    st.session_state.references.append(parsed)
    st.session_state.references.sort(key=surname_key)
    return True

# docx hyperlink helper for exports
def add_hyperlink_docx(paragraph, url, text, color="0000FF", underline=True):
    part = paragraph.part
    r_id = part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    new_run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    if color:
        c = OxmlElement("w:color"); c.set(qn("w:val"), color); rPr.append(c)
    if underline:
        u = OxmlElement("w:u"); u.set(qn("w:val"), "single"); rPr.append(u)
    new_run.append(rPr)
    t = OxmlElement("w:t"); t.text = text
    new_run.append(t)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return r_id

def generate_docx_reference_list(refs, accessed_date=""):
    from docx import Document as DocDocx
    doc = DocDocx()
    doc.add_heading("Reference List", level=1)
    for r in sorted(refs, key=surname_key):
        p = doc.add_paragraph()
        authors = r.get("authors","")
        year = r.get("year","")
        title = r.get("title","")
        source = r.get("source","")
        url = r.get("url","")
        accessed = r.get("accessed") or accessed_date or ""
        # Authors + (Year)
        header = ""
        if authors:
            header += authors
        if year:
            header += f" ({year})"
        if header:
            p.add_run(header + ". ")
        if title:
            run = p.add_run(title + ". "); run.italic = True
        if source:
            p.add_run(source + ". ")
        if url:
            p.add_run("Available at: ")
            add_hyperlink_docx(p, url, url)
            if accessed:
                p.add_run(f" (Accessed: {accessed}).")
            else:
                p.add_run(".")
    bio = BytesIO(); doc.save(bio); bio.seek(0)
    return bio

def export_as_pdf(references, accessed_date=""):
    bio = BytesIO()
    doc = SimpleDocTemplate(bio)
    styles = getSampleStyleSheet()
    elements = [Paragraph("Reference List", styles["Heading1"]), Spacer(1,8)]
    for r in sorted(references, key=surname_key):
        authors = r.get("authors","")
        year = r.get("year","")
        title = r.get("title","")
        source = r.get("source","")
        url = r.get("url","")
        accessed = r.get("accessed") or accessed_date or ""
        text_line = ""
        if authors:
            text_line += authors
        if year:
            text_line += f" ({year})"
        if title:
            text_line += f" {title}."
        if source:
            text_line += f" {source}."
        if url:
            text_line += f" Available at: {url}"
            if accessed:
                text_line += f" (Accessed: {accessed})."
        elements.append(Paragraph(text_line, styles["Normal"]))
        elements.append(Spacer(1,6))
    doc.build(elements)
    bio.seek(0)
    return bio

def export_as_xlsx(references, accessed_date=""):
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = "References"
    ws.append(["Authors","Year","Title","Source","URL","Accessed","Raw"])
    for r in sorted(references, key=surname_key):
        accessed = r.get("accessed") or accessed_date or ""
        ws.append([r.get("authors",""), r.get("year",""), r.get("title",""), r.get("source",""), r.get("url",""), accessed, r.get("raw","")])
    bio = BytesIO(); wb.save(bio); bio.seek(0)
    return bio

def export_as_txt(references, accessed_date=""):
    lines = []
    for r in sorted(references, key=surname_key):
        raw = r.get("raw") or ""
        url = r.get("url","")
        accessed = r.get("accessed") or accessed_date or ""
        line = raw
        if url:
            if accessed:
                line = f"{line} Available at: {url} (Accessed: {accessed})."
            else:
                line = f"{line} {url}"
        lines.append(line)
    return BytesIO("\n".join(lines).encode("utf-8"))

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

def scan_document_for_citations_and_mismatch(text, references):
    if not text:
        return {}
    found = set()
    # (Author, 2020)
    for m in re.finditer(r"\(([^(),\d]+?),\s*(19|20)\d{2}\)", text):
        surname = m.group(1).strip().split()[-1]; found.add(surname.lower())
    # Author (2020)
    for m in re.finditer(r"\b([A-Z][a-zA-Z-]+)\s*\((19|20)\d{2}\)", text):
        surname = m.group(1).strip(); found.add(surname.lower())
    ref_surnames = set()
    for r in references:
        auth = r.get("authors","")
        if "," in auth:
            surname = auth.split(",")[0].strip()
        else:
            surname = auth.split()[0] if auth else ""
        if surname:
            ref_surnames.add(surname.lower())
    missing_in_refs = sorted(list(found - ref_surnames))
    not_cited = sorted(list(ref_surnames - found))
    return {"found_citations": sorted(list(found)), "referenced_surnames": sorted(list(ref_surnames)), "missing_in_refs": missing_in_refs, "not_cited_in_text": not_cited}

# ---------------------------
# Navigation (sidebar)
# ---------------------------
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Home", "Check References", "Manual Input", "User Guide", "Export Results"])

# ---------------------------
# Home page
# ---------------------------
if page == "Home":
    st.header("Welcome")
    st.markdown("""
    Use the Leeds Harvard Referencing Tool to check and learn Yorkshire/Leeds Harvard referencing.
    - Upload documents (DOCX / PDF), paste your references, or add them manually.
    - The tool suggests precise Leeds Harvard corrections — students learn by making changes themselves.
    """)
    st.markdown("---")
    st.markdown("**Quick actions**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Go to Check References"):
            page = "Check References"
            st.experimental_rerun()
    with col2:
        if st.button("Open Manual Input"):
            page = "Manual Input"
            st.experimental_rerun()
    with col3:
        if st.button("User Guide"):
            page = "User Guide"
            st.experimental_rerun()

# ---------------------------
# Check References page
# ---------------------------
elif page == "Check References":
    st.header("Check References")
    st.info("Upload an assessment (DOCX or PDF) or paste text to detect citations and parse reference list. Inline fix suggestions will be shown next to each parsed entry.")

    mode = st.selectbox("Input method", ["Paste text (one reference per line)", "Upload document (DOCX/PDF)", "Fetch webpage (URL)"])
    if mode.startswith("Paste"):
        pasted = st.text_area("Paste reference list (one per line):", height=220)
        if st.button("Parse pasted references"):
            lines = [l.strip() for l in pasted.splitlines() if l.strip()]
            added = 0
            for ln in lines:
                parsed = parse_reference_string(ln)
                if add_reference(parsed):
                    added += 1
            st.success(f"Added {added} references.")
    elif mode.startswith("Upload"):
        uploaded = st.file_uploader("Upload .docx or .pdf", type=["docx","pdf"])
        if uploaded:
            st.info("Extracting text...")
            if uploaded.name.lower().endswith(".pdf"):
                txt = safe_extract_text_pdf(uploaded)
            else:
                txt = safe_extract_text_docx(uploaded)
            st.markdown("**Preview (first 1000 chars)**")
            st.text(textwrap.shorten(txt, width=1000, placeholder="..."))
            # find references section
            refs = find_reference_section(txt)
            if refs:
                st.markdown("**Detected reference lines (sample)**")
                for ln in refs[:40]:
                    st.write(ln)
                if st.button("Parse detected references and show suggestions"):
                    added = 0
                    for ln in refs:
                        parsed = parse_reference_string(ln)
                        suggestions = check_reference_for_leeds_harvard(parsed)
                        suggested_fix = format_to_leeds(parsed)
                        # display inline: original -> suggested
                        st.markdown(f"**Original:** {ln}")
                        st.markdown(f"**Suggested:** {suggested_fix}")
                        if suggestions:
                            for s in suggestions:
                                st.info(s)
                        if add_reference(parsed):
                            added += 1
                    st.success(f"Added {added} parsed references.")
            else:
                st.warning("No 'References' heading detected. You can paste references into 'Paste text' mode.")
                pasted = st.text_area("Or paste reference list here:", height=140, key="manual_paste_after_upload")
                if st.button("Parse pasted list from upload area"):
                    lines = [l.strip() for l in pasted.splitlines() if l.strip()]
                    c = 0
                    for ln in lines:
                        parsed = parse_reference_string(ln)
                        if add_reference(parsed):
                            c += 1
                    st.success(f"Added {c} references from pasted text.")
            # Run citation vs reference check on full text
            if st.button("Run citation vs reference-list check on this document"):
                results = scan_document_for_citations_and_mismatch(txt, st.session_state.references)
                st.json(results)
                if results.get("missing_in_refs"):
                    st.error("Citations in text that are NOT in the reference list:")
                    for s in results["missing_in_refs"]:
                        st.write(f"- {s} — add a full Leeds Harvard reference to the list.")
                else:
                    st.success("All in-text surnames detected appear in the reference list.")
    else:
        # URL mode
        url = st.text_input("Enter webpage URL (https://...)")
        access_date = st.text_input("Accessed date (free text, optional)")
        if st.button("Fetch & suggest"):
            if not url.strip():
                st.warning("Please enter a URL.")
            else:
                try:
                    r = requests.get(url, timeout=8)
                    s = BeautifulSoup(r.text, "html.parser")
                    title = s.title.string.strip() if s.title and s.title.string else ""
                    site = urlparse(url).netloc
                    raw = f"{site} (n.d.) {title}. {url}"
                    parsed = {"raw": raw, "authors": site, "year": "n.d.", "title": title, "source": site, "url": url, "accessed": access_date}
                    st.markdown("**Suggested Leeds Harvard entry:**")
                    st.markdown(format_to_leeds(parsed))
                    suggestions = check_reference_for_leeds_harvard(parsed)
                    if suggestions:
                        for sgg in suggestions:
                            st.info(sgg)
                    if st.button("Add this webpage reference to list"):
                        if add_reference(parsed):
                            st.success("Webpage reference added.")
                except Exception as e:
                    st.error(f"Error fetching URL: {e}")

# ---------------------------
# Manual Input page
# ---------------------------
elif page == "Manual Input":
    st.header("Manual reference entry")
    st.markdown("Add references using the forms below. All manual entries save into the shared Reference List used by Export and Checks.")

    # Tabs for Book / Journal / Report / Other
    tab = st.selectbox("Type to add:", ["Book", "Journal article", "Report / Grey literature", "Other"])
    if tab == "Book":
        b_auth = st.text_input("Author(s) (Surname, Initials)")
        b_year = st.text_input("Year")
        b_title = st.text_input("Title (book)")
        b_place = st.text_input("Place of publication (e.g. London)")
        b_publisher = st.text_input("Publisher (e.g. Routledge)")
        b_url = st.text_input("URL (optional)")
        b_accessed = st.text_input("Accessed (optional)")
        if st.button("Add Book"):
            source = f"{b_place}: {b_publisher}" if b_place or b_publisher else ""
            raw = f"{b_auth} {b_year}. {b_title}. {source}"
            if b_url:
                raw += f" {b_url}"
            parsed = {"raw": raw, "authors": b_auth, "year": b_year, "title": b_title, "source": source, "url": b_url or "", "accessed": b_accessed or ""}
            suggestions = check_reference_for_leeds_harvard(parsed)
            st.markdown("**Suggested Leeds Harvard format:**")
            st.markdown(format_to_leeds(parsed))
            if suggestions:
                for s in suggestions:
                    st.info(s)
            if add_reference(parsed):
                st.success("Book reference added.")
    elif tab == "Journal article":
        j_auth = st.text_input("Author(s)")
        j_year = st.text_input("Year")
        j_title = st.text_input("Article title")
        j_journal = st.text_input("Journal")
        j_vol = st.text_input("Volume/Issue")
        j_pages = st.text_input("Pages")
        j_url = st.text_input("DOI / URL (optional)")
        j_accessed = st.text_input("Accessed (optional)")
        if st.button("Add Journal"):
            source = ", ".join([p for p in [j_journal, j_vol, j_pages] if p])
            raw = f"{j_auth} {j_year}. {j_title}. {source}"
            if j_url:
                raw += f" {j_url}"
            parsed = {"raw": raw, "authors": j_auth, "year": j_year, "title": j_title, "source": source, "url": j_url or "", "accessed": j_accessed or ""}
            st.markdown("**Suggested Leeds Harvard format:**")
            st.markdown(format_to_leeds(parsed))
            suggestions = check_reference_for_leeds_harvard(parsed)
            if suggestions:
                for s in suggestions:
                    st.info(s)
            if add_reference(parsed):
                st.success("Journal reference added.")
    elif tab == "Report / Grey literature":
        r_org = st.text_input("Organisation / Author")
        r_year = st.text_input("Year")
        r_title = st.text_input("Title")
        r_publisher = st.text_input("Publisher / Source")
        r_url = st.text_input("URL (optional)")
        r_accessed = st.text_input("Accessed (optional)")
        if st.button("Add Report"):
            raw = f"{r_org} {r_year}. {r_title}. {r_publisher}"
            if r_url:
                raw += f" {r_url}"
            parsed = {"raw": raw, "authors": r_org, "year": r_year, "title": r_title, "source": r_publisher, "url": r_url or "", "accessed": r_accessed or ""}
            st.markdown("**Suggested Leeds Harvard format:**")
            st.markdown(format_to_leeds(parsed))
            suggestions = check_reference_for_leeds_harvard(parsed)
            if suggestions:
                for s in suggestions:
                    st.info(s)
            if add_reference(parsed):
                st.success("Report added.")
    else:
        o_auth = st.text_input("Author / Organisation")
        o_year = st.text_input("Year")
        o_title = st.text_input("Title / Description")
        o_source = st.text_input("Source / Publisher")
        o_url = st.text_input("URL (optional)")
        o_accessed = st.text_input("Accessed (optional)")
        if st.button("Add Other"):
            raw = f"{o_auth} {o_year}. {o_title}. {o_source}"
            if o_url:
                raw += f" {o_url}"
            parsed = {"raw": raw, "authors": o_auth, "year": o_year, "title": o_title, "source": o_source, "url": o_url or "", "accessed": o_accessed or ""}
            st.markdown("**Suggested Leeds Harvard format:**")
            st.markdown(format_to_leeds(parsed))
            suggestions = check_reference_for_leeds_harvard(parsed)
            if suggestions:
                for s in suggestions:
                    st.info(s)
            if add_reference(parsed):
                st.success("Reference added.")

# ---------------------------
# User Guide page
# ---------------------------
elif page == "User Guide":
    st.header("📘 Leeds Harvard Referencing Tool — User Guide")
    st.markdown(f"<div style='background:{SECONDARY_BG}; padding:10px; border-radius:8px;'>This guide explains what the tool does and how learners and tutors should use it.</div>", unsafe_allow_html=True)
    with st.expander("🎯 What this tool does"):
        st.markdown("""
        - Upload essays or reports (Word / PDF), paste references, or add references manually.
        - The tool parses references, highlights issues, and provides Leeds Harvard fix suggestions (so learners learn by correcting).
        - Exports reference lists to Word, Excel, PDF, or TXT.
        """)
    with st.expander("How to use (step-by-step)"):
        st.markdown("""
        1. Choose **Check References** from the sidebar.  
        2. Upload your document or paste reference lines.  
        3. Review inline suggestions — update your document and re-check.  
        4. When satisfied, go to **Export Results** to download the reference list.
        """)
    with st.expander("For tutors"):
        st.markdown("""
        - Use this as a teaching aid to show students examples and corrections.  
        - Encourage students to fix references themselves rather than relying on automatic fixes.  
        """)
    st.markdown("---")
    st.markdown("<div style='color:#37474f;'>If you need help, contact Macmillan Centre for Learning or your librarian.</div>", unsafe_allow_html=True)

# ---------------------------
# Export Results page
# ---------------------------
elif page == "Export Results":
    st.header("Export collected Reference List")
    st.markdown("Use the controls to download the current reference list in the required format.")
    st.write(f"References stored: {len(st.session_state.references)}")
    accessed_global = st.text_input("Default Accessed date (free text) — optional", value="")
    if st.button("Download as Word (.docx)"):
        if not st.session_state.references:
            st.warning("Reference list is empty.")
        else:
            buf = generate_docx_reference_list(st.session_state.references, accessed_global)
            st.download_button("Download Reference_List.docx", data=buf.getvalue(), file_name="Reference_List.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    if st.button("Download as PDF"):
        if not st.session_state.references:
            st.warning("Reference list is empty.")
        else:
            buf = export_as_pdf(st.session_state.references, accessed_global)
            st.download_button("Download Reference_List.pdf", data=buf.getvalue(), file_name="Reference_List.pdf", mime="application/pdf")
    if st.button("Download as Excel (XLSX)"):
        if not st.session_state.references:
            st.warning("Reference list is empty.")
        else:
            buf = export_as_xlsx(st.session_state.references, accessed_global)
            st.download_button("Download Reference_List.xlsx", data=buf.getvalue(), file_name="Reference_List.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if st.button("Download as TXT"):
        if not st.session_state.references:
            st.warning("Reference list is empty.")
        else:
            buf = export_as_txt(st.session_state.references, accessed_global)
            st.download_button("Download Reference_List.txt", data=buf.getvalue(), file_name="Reference_List.txt", mime="text/plain")

    st.markdown("---")
    if st.button("Clear all references"):
        st.session_state.references = []
        st.success("All references cleared.")

# ---------------------------
# Footer (fixed)
# ---------------------------
st.markdown(
    f"""
    <div class="footer">
        <img src="{LOGO_SMALL}" alt="Logo"> © {datetime.now().year} <a href="https://macmillancentreforlearning.co.uk" target="_blank" rel="noopener">Macmillan Centre for Learning</a>
    </div>
    """,
    unsafe_allow_html=True
)

# End of file
