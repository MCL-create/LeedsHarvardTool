import requests

def search_books(query):
    """Fetch book metadata from Google Books API."""
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
    """Fetch journal metadata from CrossRef API."""
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

def generate_book_reference(authors, year, title, publisher, city="", edition=""):
    auth_str = " and ".join(authors) if isinstance(authors, list) else authors
    ref = f"{auth_str} ({year}) {title}."
    if edition: ref += f" {edition} edn."
    if city: ref += f" {city}:"
    ref += f" {publisher}."
    return ref

def generate_journal_reference(authors, year, art_title, j_title, vol, iss, pgs):
    auth_str = " and ".join(authors) if isinstance(authors, list) else authors
    return f"{auth_str} ({year}) '{art_title}', {j_title}, {vol}({iss}), pp. {pgs}."

def generate_website_reference(authors, year, title, url, access_date):
    auth_str = " and ".join(authors) if isinstance(authors, list) else authors
    return f"{auth_str} ({year}) {title}. Available from: {url} [Accessed {access_date}]."

def get_sort_key(ref):
    return ref.lower()
