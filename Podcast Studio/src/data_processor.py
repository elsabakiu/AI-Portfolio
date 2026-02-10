# Import the Article class from the newspaper3k library
from newspaper import Article

def fetch_articles(urls):
    """
    Fetch and parse articles from a list of URLs.

    Parameters:
    - urls: list of strings, each string is a URL to an article

    Returns:
    - A list of dictionaries, each containing:
        - "url": the original URL
        - "text": the full textual content of the article

    Functionality:
    - Iterates through the list of URLs
    - For each URL:
        1. Creates an Article object
        2. Downloads the HTML content
        3. Parses the content to extract the text
        4. Appends a dictionary with the URL and text to the articles list
    - If an error occurs during download or parsing, it prints an error message
    """
    articles = []  # Initialize empty list to store article data

    for url in urls:
        try:
            article = Article(url)  # Create an Article object for the URL
            article.download()       # Download the article HTML
            article.parse()          # Extract the textual content
            # Append the result as a dictionary
            articles.append({"url": url, "text": article.text})
        except Exception as e:
            # Print any errors (e.g., network issues, invalid URL)
            print(f"Error fetching {url}: {e}")

    return articles  # Return the list of fetched articles

