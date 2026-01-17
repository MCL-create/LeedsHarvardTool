import requests
import re
from bs4 import BeautifulSoup
import docx2txt

# --- GOLD STANDARDS (Scottish Legislation & SSSC 2024) ---
GOLD_STANDARD = {
    "sssc": "Scottish Social Services Council. 2024. SSSC Codes of Practice for Social Service Workers and Employers. [Online]. [Accessed 17 Jan 2026]. Available from: https://www.sssc.uk.com",
    "care review": "Independent Care Review. 2021. The Independent Care Review: The Promise. Glasgow: Independent Care Review.",
    "standards": "Scottish Government. 2018. Health and social care standards: my support, my life. Edinburgh: Scottish Government.",
    "equality": "Great Britain. 2010. Equality Act 2010. London: The Stationery Office.",
    "data protection": "Great Britain. 2018. Data Protection Act 2018. London: The Stationery Office.",
    "health and safety": "Great Britain. 1974. Health and Safety at Work etc. Act 1974. London: HMSO."
}

def clean_text(text):
    if not text: return ""
    return re.sub(r'[^\w\s]', '', text).lower().strip()

def extract_text_from_docx(file_stream):
    """Extracts text for the Audit to ensure citations are found."""
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
    return list(set(corrected_bib))

def generate_book_reference(a, y, t, p):
    return f"{a}. {y}. {t}. {p}."

def generate_journal_reference(a, y, t, j, v, i, p):
    return f"{a}. {y}. {t}. {j}. {v} ({i}), pp.{p}."

def generate_web_reference(a, y, t, u, d):
    return f"{a}. {y}. {t}. [Online]. [Accessed {d}]. Available from: {u}"
