# leeds_harvard_tool.py

def generate_reference(author: str, year: str, title: str, publisher: str = "", place: str = "") -> str:
    """
    Generate a Leeds Harvard style reference for a book.
    
    Parameters:
        author (str): Author name(s), e.g., "Smith, J."
        year (str): Year of publication, e.g., "2023"
        title (str): Title of the book or article
        publisher (str, optional): Publisher name, e.g., "Oxford University Press"
        place (str, optional): Place of publication, e.g., "Oxford"
    
    Returns:
        str: Formatted Leeds Harvard reference.
    """
    
    # Build the reference step by step
    reference = f"{author} ({year}) {title}."
    
    if place and publisher:
        reference += f" {place}: {publisher}."
    elif publisher:
        reference += f" {publisher}."
    
    return reference.strip()
