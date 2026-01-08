# leeds_harvard_tool.py

def get_sort_key(reference_text):
    """
    Strict Leeds Alphabetical Sorting:
    Ignores 'The ', 'A ', and 'An ' at the start of corporate authors.
    """
    ref = reference_text.lower().strip()
    # Remove leading asterisks if the title comes first
    ref = ref.lstrip('*')
    
    prefixes = ['the ', 'a ', 'an ']
    for prefix in prefixes:
        if ref.startswith(prefix):
            return ref[len(prefix):]
    return ref

def format_authors(authors_list):
    """Handles the Leeds et al. rules."""
    if not authors_list:
        return "Unknown Author"
    authors = [a.strip() for a in authors_list if a.strip()]
    num = len(authors)
    if num == 1:
        return authors[0]
    elif num == 2:
        return f"{authors[0]} and {authors[1]}"
    else:
        return f"{authors[0]} et al."

def generate_book_reference(authors, year, title, publisher, place, edition=""):
    auth_str = format_authors(authors)
    ed_clean = edition.lower().replace("edition", "edn.").replace("ed.", "edn.")
    ed_str = f" {ed_clean}" if edition else ""
    return f"{auth_str} ({year}) *{title}*.{ed_str} {place}: {publisher}."

def generate_journal_reference(authors, year, art_title, jou_title, vol, iss, pgs):
    auth_str = format_authors(authors)
    return f"{auth_str} ({year}) {art_title}. *{jou_title}*. **{vol}**({iss}), pp.{pgs}."

def generate_website_reference(authors, year, title, url, accessed_date):
    auth_str = format_authors(authors)
    return f"{auth_str} ({year}) *{title}*. [Online]. [Accessed {accessed_date}]. Available from: {url}"
