import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import random
import re
from urllib.parse import urljoin

class GamesRadarScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # RSS feeds from GamesRadar – these are real URLs, not hardcoded data
        self.rss_feeds = [
            "https://www.gamesradar.com/uk/feeds/latest/news/",
            "https://www.gamesradar.com/uk/feeds/latest/reviews/",
            "https://www.gamesradar.com/feeds/latest/news/",
            "https://www.gamesradar.com/feeds/latest/reviews/",
            "https://www.gamesradar.com/uk/feeds/games/",
            "https://www.gamesradar.com/feeds/games/"
        ]

    def scrape_from_url(self, target_url=None, count=10):
        """
        Scrape articles from GamesRadar RSS feeds, then extract detailed fields.
        target_url is ignored – we always use RSS feeds for reliability.
        """
        print("\n🎮 SCRAPING FROM GAMESRADAR RSS FEEDS")
        all_articles = []

        for feed_url in self.rss_feeds:
            try:
                print(f"📡 Fetching RSS: {feed_url}")
                resp = requests.get(feed_url, headers=self.headers, timeout=10)
                root = ET.fromstring(resp.content)

                for item in root.findall('.//item'):
                    title = item.find('title')
                    link = item.find('link')
                    pubDate = item.find('pubDate')
                    if title is not None and link is not None and title.text and link.text:
                        all_articles.append({
                            'url': link.text,
                            'title': title.text,
                            'date': pubDate.text if pubDate is not None else ''
                        })
            except Exception as e:
                print(f"RSS error {feed_url}: {e}")
                continue

        print(f"✅ Found {len(all_articles)} raw articles from RSS")

        # Remove duplicates by URL
        seen = set()
        unique_articles = []
        for a in all_articles:
            if a['url'] not in seen:
                seen.add(a['url'])
                unique_articles.append(a)

        if not unique_articles:
            return []

        # Select random articles
        selected = random.sample(unique_articles, min(count, len(unique_articles)))

        # For each selected article, fetch the page and extract required fields
        scraped_games = []
        for article in selected:
            try:
                print(f"🔍 Processing: {article['title'][:60]}...")
                resp = requests.get(article['url'], headers=self.headers, timeout=10)
                soup = BeautifulSoup(resp.text, 'html.parser')

                # Remove scripts/styles
                for tag in soup(["script", "style"]):
                    tag.decompose()

                text = soup.get_text()

                # 1. Game Title (from h1 or fallback to RSS title)
                game_title = article['title']
                h1 = soup.find('h1')
                if h1:
                    game_title = h1.get_text().strip()

                # 2. Release Date (search in article text)
                release_date = "Not Available"
                date_patterns = [
                    r'release date:?\s*([^.]+)',
                    r'launch(?:es)?:?\s*([^.]+)',
                    r'out now:?\s*([^.]+)',
                    r'coming:?\s*([^.]+)',
                    r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b'
                ]
                for pat in date_patterns:
                    m = re.search(pat, text, re.IGNORECASE)
                    if m:
                        release_date = m.group(0).strip()
                        break

                # 3. Key Features (look for bullet points or first paragraphs)
                key_features = []
                # Look for list items that might be features
                for li in soup.find_all('li'):
                    li_text = li.get_text().strip()
                    if 20 < len(li_text) < 200 and any(kw in li_text.lower() for kw in ['feature', 'gameplay', 'include']):
                        key_features.append(li_text)
                # If not enough, take first few paragraphs
                if len(key_features) < 3:
                    for p in soup.find_all('p')[:5]:
                        p_text = p.get_text().strip()
                        if 30 < len(p_text) < 250:
                            key_features.append(p_text[:150] + "…" if len(p_text) > 150 else p_text)
                key_features = key_features[:4] or ["Not Available"]

                # 4. Platform Availability
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
                for plat, keywords in platform_keywords.items():
                    if any(kw in text_lower for kw in keywords):
                        platforms.append(plat)
                if not platforms:
                    platforms = ["Not Available"]

                # 5. Developer Information
                developer = "Not Available"
                dev_match = re.search(r'developer:?\s*([^.]+)', text, re.IGNORECASE)
                if dev_match:
                    developer = dev_match.group(1).strip()

                # 6. Publisher Information
                publisher = "Not Available"
                pub_match = re.search(r'publisher:?\s*([^.]+)', text, re.IGNORECASE)
                if pub_match:
                    publisher = pub_match.group(1).strip()

                scraped_games.append({
                    'game_title': game_title[:150],
                    'release_date': release_date,
                    'key_features': key_features,
                    'platform_availability': platforms,
                    'developer_info': developer,
                    'publisher_info': publisher,
                    'article_url': article['url']
                })
            except Exception as e:
                print(f"Error processing {article['url']}: {e}")
                # Still include a minimal entry with "Not Available"
                scraped_games.append({
                    'game_title': article['title'][:150],
                    'release_date': "Not Available",
                    'key_features': ["Not Available"],
                    'platform_availability': ["Not Available"],
                    'developer_info': "Not Available",
                    'publisher_info': "Not Available",
                    'article_url': article['url']
                })

        return scraped_games
