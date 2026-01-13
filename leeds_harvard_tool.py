import requests
import re
from bs4 import BeautifulSoup

# --- MCL MASTER CORRECTION MAP (The Gold Standard) ---
# Verified references for Scottish Social Care and UK Legislation
GOLD_STANDARD = {
    "bee": "Bee, H. and Boyd, D. (2002) Life Span Development. 3rd ed. London: Allyn and Bacon.",
    "sssc": "Scottish Social Services Council (2024) SSSC Codes of Practice for Social Service Workers and Employers. [Online]. [Accessed 13 Jan 2026]. Available from: https://www.sssc.uk.com",
    "care review": "Independent Care Review (2021) The Independent Care Review: The Promise. Glasgow: Independent Care Review.",
    "standards": "Scottish Government (2018) Health and Social Care Standards: my support, my life. Edinburgh: Scottish Government.",
    "thompson": "Thompson, N. (2005) Understanding Social Work: Preparing for Practice. 2nd ed. Basingstoke: Palgrave Macmillan.",
    "equality": "Great Britain (2010) Equality Act 2010. London: The Stationery Office.",
    "data protection": "Great Britain (2018) Data Protection Act 2018. London: The Stationery Office.",
    "health and safety": "Great Britain (1974) Health and Safety at Work etc. Act 1974. London: HMSO."
}

def clean_text(text):
    """Standardizes text for fuzzy matching by removing formatting and clutter."""
    if not text: return ""
    # Simplify by taking the first part of the title and removing punctuation/case
    text = re.split(r'[:|–|-]', text)[0]
    return re.sub(r'[^\w\s]', '', text).lower().strip()

def apply_one_click_corrections(current_bib):
    """Replaces messy entries with the full correct Leeds Harvard version."""
    corrected_bib = []
    for entry in current_bib:
        cleaned_entry = clean_text(entry)
        match_found = False
        for key, gold_ref in GOLD_STANDARD.items():
            if key in cleaned_entry:
                corrected_bib.append(gold_ref)
                match_found = True
                break
        if not match_found:
            corrected_bib.append(entry)
    return list(set(corrected_bib))

def search_books(query):
    """Google Books API search with query cleaning to ignore edition/city."""
    clean_query = query.lower().replace("3rd ed", "").replace("london", "").strip()
    url = f"https://www.googleapis.com/books/v1/volumes?q={clean_query}&maxResults=3"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        results = []
        for item in data.get('items', []):
            info = item.get('volumeInfo', {})
            results.append({
                'label': f"{info.get('title')} ({info.get('publishedDate', 'N/A')[:4]})",
                'authors': ", ".join(info.get('authors', ["Unknown Author"])),
                'year': info.get('publishedDate', 'N/A')[:4],
                'title': info.get('title', 'N/A'),
                'publisher': info.get('publisher', 'N/A')
            })
        return results
    except: return []

def generate_book_reference(authors, year, title, publisher, edition=""):
    ref = f"{authors} ({year}) {title}."
    if edition: ref += f" {edition} edn."
    ref += f" {publisher}."
    return ref

def generate_website_reference(authors, year, title, url, access_date):
    return f"{authors} ({year}) {title}. [Online]. [Accessed {access_date}]. Available from: {url}"

def get_sort_key(ref):
    return ref.lower()
