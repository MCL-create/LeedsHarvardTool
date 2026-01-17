import re
import docx2txt

# --- GOLD STANDARDS (Scottish Legislation & SSSC) ---
GOLD_STANDARD = {
    "sssc": "Scottish Social Services Council. 2024. <i>Codes of practice for social service workers and employers</i>. Available at: https://www.sssc.uk.com/codes-of-practice (Accessed: 13 January 2026).",
    "care review": "Independent Care Review. 2021. <i>The Independent Care Review: The Promise</i>. Glasgow: Independent Care Review.",
    "standards": "Scottish Government. 2018. <i>Health and social care standards: my support, my life</i>. Edinburgh: Scottish Government.",
    "equality": "Great Britain. 2010. <i>Equality Act 2010</i>. London: The Stationery Office.",
    "data protection": "Great Britain. 2018. <i>Data Protection Act 2018</i>. London: The Stationery Office.",
    "health and safety": "Great Britain. 1974. <i>Health and Safety at Work etc. Act 1974</i>. London: HMSO."
}

def clean_text(text):
    if not text: return ""
    return re.sub(r'[^\w\s]', '', text).lower().strip()

def extract_text_from_docx(file_stream):
    """Essential for the Smart Audit to read essay content."""
    try:
        return docx2txt.process(file_stream)
    except:
        return ""

def apply_one_click_corrections(current_bib):
    corrected_bib = []
    for entry in current_bib:
        cleaned_entry = clean_text(entry)
        match_found = False
        for key, gold_ref in GOLD_STANDARD.items():
            if key in cleaned_entry:
                corrected_bib.append(gold_ref)
                match_found = True
                break
        if not match_found: corrected_bib.append(entry)
    return sorted(list(set(corrected_bib)))

def generate_book_reference(a, y, t, p):
    return f"{a}. ({y}) <i>{t}</i>. {p}."

def generate_journal_reference(a, y, t, j, v, i, p):
    return f"{a}. ({y}) ‘{t}’, <i>{j}</i>, {v}({i}), pp. {p}."

def generate_web_reference(a, y, t, u, d):
    return f"{a}. ({y}) <i>{t}</i>. Available at: {u} (Accessed: {d})."
