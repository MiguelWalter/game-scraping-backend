import requests
from bs4 import BeautifulSoup
import random
import re
import time
from urllib.parse import urljoin

class GamesRadarScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_from_url(self, target_url, count=10):
        """Scrape real articles from GamesRadar"""
        print(f"\n🎮 SCRAPING FROM: {target_url}")
        
        try:
            # Get the page
            print(f"📡 Fetching: {target_url}")
            response = self.session.get(target_url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find ALL article links
            all_articles = []
            
            # Find all article tags
            articles = soup.find_all('article')
            print(f"📊 Found {len(articles)} article tags")
            
            for article in articles:
                link = article.find('a')
                if link and link.get('href'):
                    href = link['href']
                    if not href.startswith('http'):
                        href = urljoin(target_url, href)
                    
                    # Get title
                    title_elem = article.find('h3') or article.find('h2')
                    title = title_elem.text.strip() if title_elem else link.text.strip()
                    
                    if 'gamesradar.com' in href and len(title) > 10:
                        all_articles.append({
                            'url': href,
                            'title': title
                        })
            
            # Find links that look like articles
            for link in soup.find_all('a', href=True):
                href = link['href']
                if not href.startswith('http'):
                    href = urljoin(target_url, href)
                
                text = link.text.strip()
                
                if ('gamesradar.com' in href and 
                    len(text) > 20 and
                    any(x in href for x in ['/news/', '/reviews/', '/games/'])):
                    
                    if not any(a['url'] == href for a in all_articles):
                        all_articles.append({
                            'url': href,
                            'title': text
                        })
            
            # Remove duplicates
            seen = set()
            unique = []
            for article in all_articles:
                if article['url'] not in seen:
                    seen.add(article['url'])
                    unique.append(article)
            
            print(f"✅ Found {len(unique)} unique articles")
            
            if len(unique) == 0:
                print("❌ No articles found")
                return []
            
            # Select random articles
            if len(unique) >= count:
                selected = random.sample(unique, count)
            else:
                selected = unique
            
            # Extract info from articles
            games = []
            for article in selected:
                try:
                    # Try to get detailed info
                    game_info = self.extract_info(article['url'], article['title'])
                    if game_info:
                        games.append(game_info)
                except:
                    # Fallback to basic info
                    games.append({
                        'game_title': article['title'][:100],
                        'release_date': 'Not Available',
                        'key_features': ['Not Available'],
                        'platform_availability': ['Not Available'],
                        'developer_info': 'Not Available',
                        'publisher_info': 'Not Available',
                        'article_url': article['url']
                    })
                time.sleep(0.5)
            
            return games
            
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def extract_info(self, url, title):
        """Extract detailed info from article"""
        response = self.session.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove scripts
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text()
        
        # Title
        game_title = title
        h1 = soup.find('h1')
        if h1:
            game_title = h1.text.strip()
        
        # Release Date
        release_date = "Not Available"
        date_patterns = [
            r'release date:?\s*([^.]+)',
            r'launch:?\s*([^.]+)',
            r'out now:?\s*([^.]+)',
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                release_date = match.group(0).strip()
                break
        
        # Platforms
        platforms = []
        platform_list = ['PS5', 'PS4', 'Xbox', 'Switch', 'PC']
        for platform in platform_list:
            if platform.lower() in text.lower():
                platforms.append(platform)
        if not platforms:
            platforms = ["Not Available"]
        
        # Developer
        developer = "Not Available"
        dev_match = re.search(r'developer:?\s*([^.]+)', text, re.IGNORECASE)
        if dev_match:
            developer = dev_match.group(1).strip()
        
        # Publisher
        publisher = "Not Available"
        pub_match = re.search(r'publisher:?\s*([^.]+)', text, re.IGNORECASE)
        if pub_match:
            publisher = pub_match.group(1).strip()
        
        # Features
        features = []
        for p in soup.find_all('p')[:3]:
            p_text = p.text.strip()
            if len(p_text) > 30:
                features.append(p_text[:150] + "..." if len(p_text) > 150 else p_text)
        if not features:
            features = ["Not Available"]
        
        return {
            'game_title': game_title[:100],
            'release_date': release_date,
            'key_features': features[:3],
            'platform_availability': platforms,
            'developer_info': developer,
            'publisher_info': publisher,
            'article_url': url
        }
