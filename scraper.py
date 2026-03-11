import requests
from bs4 import BeautifulSoup
import random
from urllib.parse import urljoin, urlparse

def get_random_articles(base_url, max_articles=10):
    """
    Fetch a GamesRadar page and return up to `max_articles` random article URLs.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Error fetching the page: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    article_links = set()

    # Common article path patterns on GamesRadar
    article_patterns = ['/news/', '/features/', '/reviews/', '/gaming/', '/how-to/', '/guides/']

    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # Must be on gamesradar.com domain
        if 'gamesradar.com' not in parsed.netloc:
            continue

        # Check if path contains any of the article patterns
        if any(pattern in parsed.path for pattern in article_patterns):
            # Avoid duplicates and non-article pages (e.g., main sections)
            if not parsed.path.endswith(('/news/', '/features/', '/reviews/', '/gaming/')):
                article_links.add(full_url)

    # Convert to list and shuffle
    article_list = list(article_links)
    random.shuffle(article_list)

    if not article_list:
        print("No articles found on this page. Try a different GamesRadar URL.")
        return []

    selected = article_list[:max_articles]
    print(f"Found {len(article_list)} articles. Showing {len(selected)} random:")
    for i, url in enumerate(selected, 1):
        print(f"{i}. {url}")

    return selected

if __name__ == "__main__":
    url = input("Enter GamesRadar URL: ").strip()
    get_random_articles(url)
