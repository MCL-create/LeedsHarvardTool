import requests
import re
from bs4 import BeautifulSoup

# --- MCL MASTER CORRECTION MAP (Verified Gold Standards) ---
GOLD_STANDARD = {
    "bee": "Bee, H. and Boyd, D. 2002. Life span development. 3rd ed. London: Allyn and Bacon.",
    "sssc": "Scottish Social Services Council. 2024. SSSC Codes of Practice for Social Service Workers and Employers. [Online]. [Accessed 16 Jan 2026]. Available from: https://www.sssc.uk.com",
    "care review": "Independent Care Review. 2021. The Independent Care Review: The Promise. Glasgow: Independent Care Review.",
    "standards": "Scottish Government. 2018. Health and social care standards: my support, my life. Edinburgh: Scottish Government.",
    "equality": "Great Britain. 2010. Equality Act 2010. London: The Stationery Office.",
    "data protection": "Great Britain. 2018. Data Protection Act 2018. London: The Stationery Office.",
    "health and safety": "Great Britain. 1974. Health and Safety at Work etc. Act 1974. London: HMSO."
}

def clean_text(text):
    if not text: return ""
    return re.sub(r'[^\w\s]', '', text).lower().strip()

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

def generate_book_reference(a, y, t, p, ed="", ser="", vol=""):
    ref = f"{a}. {y}. {t}."
    if ser: ref += f" {ser},"
    if vol: ref += f" Vol {vol}."
    if ed: ref += f" {ed}."
    ref += f" {p}."
    return ref

def generate_journal_reference(a, y, t, j, v, i, p):
    return f"{a}. {y}. {t}. {j}. {v} ({i}), pp.{p}."

def generate_web_reference(a, y, t, u, d):
    return f"{a}. {y}. {t}. [Online]. [Accessed {d}]. Available from: {u}"

def search_books(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&maxResults=3"
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

def scrape_website(url):
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.title.string if soup.title else "Unknown Title"
        year_match = re.search(r'20\d{2}', res.text)
        year = year_match.group(0) if year_match else "no date"
        return {"title": title.strip(), "year": year}
    except: return {"title": "", "year": ""}
