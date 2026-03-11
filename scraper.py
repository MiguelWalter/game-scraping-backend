import requests
import json
import re
import random
from urllib.parse import urljoin

class GamesRadarScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_from_url(self, target_url, count=10):
        """Extract articles from JSON embedded in the page"""
        print(f"\n🎮 SCRAPING FROM: {target_url}")
        
        try:
            # Fetch the page
            response = self.session.get(target_url, timeout=15)
            html = response.text
            
            # Try to find JSON-LD data (common for article listings)
            articles = []
            
            # Method 1: Look for JSON-LD script tags
            json_ld_matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
            for match in json_ld_matches:
                try:
                    data = json.loads(match)
                    # Handle different JSON-LD structures
                    if isinstance(data, dict):
                        if '@graph' in data:
                            for item in data['@graph']:
                                if item.get('@type') == 'Article' and 'url' in item:
                                    articles.append({
                                        'url': item['url'],
                                        'title': item.get('headline', '')
                                    })
                        elif data.get('@type') == 'Article':
                            articles.append({
                                'url': data.get('url', ''),
                                'title': data.get('headline', '')
                            })
                    elif isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Article':
                                articles.append({
                                    'url': item.get('url', ''),
                                    'title': item.get('headline', '')
                                })
                except:
                    continue
            
            # Method 2: Look for Next.js data (common in modern sites)
            next_data_matches = re.findall(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
            for match in next_data_matches:
                try:
                    data = json.loads(match)
                    # Navigate through the complex structure to find articles
                    # This is site-specific and may need adjustment
                    props = data.get('props', {})
                    page_props = props.get('pageProps', {})
                    # Look for article lists in various places
                    for key, value in page_props.items():
                        if isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict) and 'url' in item and 'title' in item:
                                    articles.append({
                                        'url': urljoin(target_url, item['url']),
                                        'title': item['title']
                                    })
                except:
                    continue
            
            # Method 3: Fallback – look for <a> tags with article-like URLs
            if len(articles) < count:
                # Simple regex to find links that look like articles
                link_pattern = r'<a[^>]+href="([^"]+)"[^>]*>([^<]+)</a>'
                for url, title in re.findall(link_pattern, html):
                    if ('/news/' in url or '/reviews/' in url or '/games/' in url) and len(title) > 15:
                        full_url = urljoin(target_url, url)
                        articles.append({
                            'url': full_url,
                            'title': title.strip()
                        })
            
            # Remove duplicates and filter
            seen = set()
            unique_articles = []
            for a in articles:
                if a['url'] and a['url'] not in seen and len(a['title']) > 10:
                    seen.add(a['url'])
                    unique_articles.append(a)
            
            print(f"✅ Found {len(unique_articles)} unique articles via JSON")
            
            if not unique_articles:
                print("❌ No articles found")
                return []
            
            # Select random articles
            if len(unique_articles) >= count:
                selected = random.sample(unique_articles, count)
            else:
                selected = unique_articles
            
            # Return with placeholder info (you can enhance this later)
            games = []
            for article in selected:
                games.append({
                    'game_title': article['title'][:100],
                    'release_date': 'See article',
                    'key_features': ['Read full article for details'],
                    'platform_availability': ['Check article'],
                    'developer_info': 'See article',
                    'publisher_info': 'See article',
                    'article_url': article['url']
                })
            
            return games
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
