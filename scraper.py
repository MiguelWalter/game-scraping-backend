import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin
import random

class GamesRadarScraper:
    def __init__(self):
        self.base_url = "https://www.gamesradar.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_random_games(self, count=10):
        """Scrape random game articles from GamesRadar"""
        print("\n" + "="*60)
        print("🎮 SCRAPING RANDOM GAMES FROM GAMESRADAR")
        print("="*60)
        
        all_games = []
        
        # Sources to scrape from
        sources = [
            "/games/",
            "/news/",
            "/reviews/",
            "/features/",
            "/category/pc-gaming/",
            "/category/ps5/",
            "/category/xbox-series-x/",
            "/category/nintendo-switch/"
        ]
        
        # Shuffle sources for randomness
        random.shuffle(sources)
        
        for source in sources:
            try:
                url = urljoin(self.base_url, source)
                print(f"📡 Checking: {url}")
                
                response = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find all article links
                articles = soup.find_all('article')
                
                for article in articles:
                    link = article.find('a', href=True)
                    if link:
                        href = link['href']
                        if not href.startswith('http'):
                            href = urljoin(self.base_url, href)
                        
                        # Get title
                        title_elem = article.find('h3') or article.find('h2')
                        title = title_elem.get_text().strip() if title_elem else link.get_text().strip()
                        
                        if title and len(title) > 10:
                            # Check if it's a game article
                            if any(word in href.lower() for word in ['/games/', '/reviews/', '/news/']):
                                game_info = self.extract_game_info(href, title)
                                if game_info:
                                    all_games.append(game_info)
                                    print(f"  ✅ Found: {title[:50]}...")
                                    
                                    if len(all_games) >= count:
                                        return all_games[:count]
                
                time.sleep(1)
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue
        
        # If we don't have enough, get from different sources
        while len(all_games) < count:
            all_games.append(self.get_fallback_game())
        
        return all_games[:count]
    
    def extract_game_info(self, url, title):
        """Extract game information from article"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # Get game title
            game_title = title
            h1 = soup.find('h1')
            if h1:
                game_title = h1.get_text().strip()
            
            # Get release date
            release_date = "Not Available"
            date_patterns = [
                r'release date:?\s*([^.]+)',
                r'launch(?:es)?:?\s*([^.]+)',
                r'out now:?\s*([^.]+)',
                r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s*\d{4}\b'
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    release_date = match.group(0)
                    break
            
            # Get platforms
            platforms = []
            platform_list = ['PS5', 'PS4', 'Xbox Series X', 'Xbox One', 'Nintendo Switch', 'PC']
            
            for platform in platform_list:
                if platform.lower() in text.lower():
                    platforms.append(platform)
            
            if not platforms:
                platforms = ["Platform information not available"]
            
            # Get developer
            developer = "Not Available"
            dev_match = re.search(r'developer:?\s*([^.]+)', text, re.IGNORECASE)
            if dev_match:
                developer = dev_match.group(1).strip()
            
            # Get publisher
            publisher = "Not Available"
            pub_match = re.search(r'publisher:?\s*([^.]+)', text, re.IGNORECASE)
            if pub_match:
                publisher = pub_match.group(1).strip()
            
            # Get key features
            features = []
            paragraphs = soup.find_all('p')
            for p in paragraphs[:3]:
                p_text = p.get_text().strip()
                if len(p_text) > 30:
                    features.append(p_text[:150] + "..." if len(p_text) > 150 else p_text)
            
            if not features:
                features = ["Read the full article for details"]
            
            return {
                'game_title': game_title[:100],
                'release_date': release_date,
                'platform_availability': platforms,
                'developer_info': developer,
                'publisher_info': publisher,
                'key_features': features[:3],
                'article_url': url
            }
            
        except Exception as e:
            print(f"Error extracting: {e}")
            return None
    
    def get_fallback_game(self):
        """Fallback game if scraping fails"""
        return {
            'game_title': "Random Game Article",
            'release_date': "Check GamesRadar",
            'platform_availability': ["Multiple Platforms"],
            'developer_info': "See article",
            'publisher_info': "See article",
            'key_features': ["Click the link to read the full article on GamesRadar"],
            'article_url': "https://www.gamesradar.com"
        }
