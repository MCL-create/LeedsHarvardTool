# leeds_harvard_tool.py

def format_authors(authors_list):
    """
    Formats a list of authors according to Leeds Harvard rules:
    - 1 author: Smith, J.
    - 2 authors: Smith, J. and Jones, P.
    - 3+ authors: Smith, J. et al.
    """
    if not authors_list:
        return "Unknown Author"
    
    # Clean whitespace from each author name
    authors = [a.strip() for a in authors_list if a.strip()]
    
    num_authors = len(authors)
    
    if num_authors == 1:
        return authors[0]
    elif num_authors == 2:
        return f"{authors[0]} and {authors[1]}"
    else:
        return f"{authors[0]} et al."

def generate_book_reference(authors, year, title, publisher, place, edition=""):
    """
    Generates a reference for a printed book.
    Format: Author(s) (Year) Title. Edition (if not 1st). Place: Publisher.
    """
    auth_str = format_authors(authors)
    
    # Leeds style: Titles are italicized. Edition is only included if not the 1st.
    # We use * for markdown italics which Streamlit and GitHub render correctly.
    ref = f"{auth_str} ({year}) *{title}*."
    
    if edition:
        # Standardize edition format (e.g., '2nd edn.')
        ed_clean = edition.lower().replace("edition", "edn.").replace("ed.", "edn.")
        ref += f" {ed_clean}"
        
    ref += f" {place}: {publisher}."
    
    return ref

def generate_journal_reference(authors, year, article_title, journal_title, volume, issue, pages):
    """
    Generates a reference for a journal article.
    Format: Author(s) (Year) Article title. Journal Title. Volume(Issue), pp.pages.
    """
    auth_str = format_authors(authors)
    
    # Article title is plain, Journal Title is italicized
    ref = f"{auth_str} ({year}) {article_title}. *{journal_title}*. **{volume}**({issue}), pp.{pages}."
    
    return ref

def generate_website_reference(authors, year, title, url, accessed_date):
    """
    Generates a reference for a website.
    Format: Author(s) (Year) Title. [Online]. [Accessed date]. Available from: URL
    """
    auth_str = format_authors(authors)
    
    ref = f"{auth_str} ({year}) *{title}*. [Online]. [Accessed {accessed_date}]. Available from: {url}"
    
    return ref
