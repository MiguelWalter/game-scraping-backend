import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin

class GamesRadarScraper:
    def __init__(self):
        self.base_url = "https://www.gamesradar.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_article_links(self, url, max_links=20):
        """Extract article links from a GamesRadar page (e.g. homepage, news section)"""
        print(f"📡 Fetching article list from: {url}")
        try:
            resp = self.session.get(url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            links = []

            # Common article containers on GamesRadar
            containers = soup.find_all(['article', 'div'], class_=re.compile(r'listingResult|result|article|card'))
            for article in containers:
                link_tag = article.find('a', href=True)
                if link_tag:
                    href = link_tag['href']
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(self.base_url, href)

                    # Extract title
                    title_elem = article.find(['h3', 'h2', 'h4'], class_=re.compile(r'title|name|headline'))
                    title = title_elem.get_text().strip() if title_elem else link_tag.get_text().strip()

                    if 'gamesradar.com' in full_url and len(title) > 10:
                        links.append({'url': full_url, 'title': title})

            # Remove duplicates
            seen = set()
            unique = []
            for link in links:
                if link['url'] not in seen:
                    seen.add(link['url'])
                    unique.append(link)

            print(f"✅ Found {len(unique)} article links")
            return unique[:max_links]
        except Exception as e:
            print(f"❌ Error fetching article list: {e}")
            return []

    def extract_game_info(self, article_url, article_title):
        """Extract all required fields from a single article page"""
        try:
            print(f"  📄 Processing: {article_title[:60]}...")
            resp = self.session.get(article_url, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Remove scripts/styles
            for tag in soup(['script', 'style']):
                tag.decompose()

            text = soup.get_text()

            # 1. Game Title – prefer H1, otherwise use link title
            game_title = article_title
            h1 = soup.find('h1')
            if h1:
                game_title = h1.get_text().strip()

            # 2. Release Date
            release_date = "Not Available"
            date_patterns = [
                r'release date:?\s*([^.]+)',
                r'launch(?:es)?:?\s*([^.]+)',
                r'out now:?\s*([^.]+)',
                r'coming:?\s*([^.]+)',
                r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b'
            ]
            for pat in date_patterns:
                match = re.search(pat, text, re.IGNORECASE)
                if match:
                    release_date = match.group(0).strip()
                    break

            # 3. Key Features – look for list items or paragraphs with feature keywords
            features = []
            for li in soup.find_all('li'):
                li_text = li.get_text().strip()
                if 20 < len(li_text) < 200 and any(k in li_text.lower() for k in ['feature', 'gameplay', 'include', 'allows']):
                    features.append(li_text)
            if len(features) < 3:
                for p in soup.find_all('p')[:5]:
                    p_text = p.get_text().strip()
                    if 30 < len(p_text) < 250:
                        features.append(p_text[:150] + "…" if len(p_text) > 150 else p_text)
            features = features[:4] or ["Not Available"]

            # 4. Platforms
            platforms = []
            platform_keywords = {
                'PS5': ['ps5', 'playstation 5'],
                'PS4': ['ps4', 'playstation 4'],
                'Xbox Series X|S': ['xbox series'],
                'Xbox One': ['xbox one'],
                'Nintendo Switch': ['switch', 'nintendo switch'],
                'PC': ['pc', 'steam', 'windows']
            }
            text_lower = text.lower()
            for plat, keys in platform_keywords.items():
                if any(k in text_lower for k in keys):
                    platforms.append(plat)
            if not platforms:
                platforms = ["Not Available"]

            # 5. Developer
            developer = "Not Available"
            dev_match = re.search(r'developer:?\s*([^.]+)', text, re.IGNORECASE)
            if dev_match:
                developer = dev_match.group(1).strip()

            # 6. Publisher
            publisher = "Not Available"
            pub_match = re.search(r'publisher:?\s*([^.]+)', text, re.IGNORECASE)
            if pub_match:
                publisher = pub_match.group(1).strip()

            return {
                'game_title': game_title[:150],
                'release_date': release_date,
                'key_features': features,
                'platform_availability': platforms,
                'developer_info': developer,
                'publisher_info': publisher,
                'article_url': article_url
            }
        except Exception as e:
            print(f"    ✗ Error extracting info: {e}")
            return None

    def scrape_games(self, start_url, max_games=10):
        """Main method – returns at least 10 games from the given GamesRadar URL"""
        print("\n" + "="*70)
        print("🎮 GAMESRADAR SCRAPER")
        print("="*70)
        article_links = self.get_article_links(start_url, max_links=max_games*2)
        if not article_links:
            print("❌ No article links found.")
            return []

        scraped = []
        for i, link in enumerate(article_links):
            if len(scraped) >= max_games:
                break
            print(f"\n📊 Article {i+1}/{len(article_links)}")
            game_info = self.extract_game_info(link['url'], link['title'])
            if game_info:
                scraped.append(game_info)
            time.sleep(1)  # Be polite

        print(f"\n✅ Scraped {len(scraped)} games (requested {max_games})")
        return scraped
