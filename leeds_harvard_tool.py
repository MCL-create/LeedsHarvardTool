import requests
import re
from bs4 import BeautifulSoup

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
                'authors': ", ".join(info.get('authors', ["Unknown"])),
                'year': info.get('publishedDate', 'N/A')[:4],
                'title': info.get('title', 'N/A'),
                'publisher': info.get('publisher', 'N/A')
            })
        return results
    except:
        return []

def search_journals(query):
    url = f"https://api.crossref.org/works?query={query}&rows=3"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        results = []
        for item in data.get('message', {}).get('items', []):
            title = item.get('title', ['N/A'])[0]
            year = str(item.get('created', {}).get('date-parts', [[0]])[0][0])
            author_list = [f"{a.get('family', '')}, {a.get('given', '')[0]}" for a in item.get('author', []) if 'family' in a]
            results.append({
                'label': f"{title} ({year})",
                'authors': ", ".join(author_list) if author_list else "Unknown",
                'year': year,
                'title': title,
                'journal': item.get('container-title', ['N/A'])[0],
                'vol': item.get('volume', ''),
                'iss': item.get('issue', ''),
                'pgs': item.get('page', '')
            })
        return results
    except:
        return []

def scrape_website_metadata(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else "Unknown Title"
        year_match = re.search(r'20\d{2}', response.text)
        year = year_match.group(0) if year_match else "no date"
        return {"title": title.strip(), "year": year}
    except:
        return {"title": "", "year": ""}

def generate_book_reference(authors, year, title, publisher):
    return f"{authors} ({year}) {title}. {publisher}."

def generate_journal_reference(authors, year, art_title, j_title, vol, iss, pgs):
    return f"{authors} ({year}) '{art_title}', {j_title}, {vol}({iss}), pp. {pgs}."

def generate_website_reference(authors, year, title, url, access_date):
    return f"{authors} ({year}) {title}. Available from: {url} [Accessed {access_date}]."

def get_sort_key(ref):
    return ref.lower()
