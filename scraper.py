import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import random
import time

class GamesRadarScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_from_url(self, target_url, count=10):
        """Scrape random game articles from GamesRadar"""
        print(f"\n🎮 SCRAPING FROM: {target_url}")
        
        # Use main GamesRadar URL
        base_url = "https://www.gamesradar.com/"
        
        try:
            # Fetch page
            response = self.session.get(base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all article links
            all_articles = []
            
            # Look for article tags first
            articles = soup.find_all('article')
            for article in articles:
                link = article.find('a', href=True)
                if link:
                    href = link['href']
                    if not href.startswith('http'):
                        href = urljoin(base_url, href)
                    
                    title_elem = article.find('h3') or article.find('h2')
                    title = title_elem.get_text().strip() if title_elem else link.get_text().strip()
                    
                    if 'gamesradar.com' in href and len(title) > 10:
                        all_articles.append({
                            'url': href,
                            'title': title
                        })
            
            # Also look for links
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().strip()
                
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                if ('gamesradar.com' in href and 
                    len(text) > 15 and
                    any(x in href for x in ['/news/', '/reviews/', '/games/'])):
                    
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
            
            if not unique:
                return []
            
            # Select random articles
            if len(unique) >= count:
                selected = random.sample(unique, count)
            else:
                selected = unique
            
            # Extract info
            scraped = []
            for article in selected:
                try:
                    # Try to get more details
                    game_info = self.extract_basic_info(article['url'], article['title'])
                    if game_info:
                        scraped.append(game_info)
                except:
                    # If detailed extraction fails, use basic info
                    scraped.append({
                        'game_title': article['title'][:100],
                        'release_date': 'Check article',
                        'key_features': ['Read full article for details'],
                        'platform_availability': ['See article'],
                        'developer_info': 'See article',
                        'publisher_info': 'See article',
                        'article_url': article['url']
                    })
                time.sleep(0.5)
            
            return scraped[:count]
            
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def extract_basic_info(self, url, title):
        """Extract basic info from article"""
        try:
            response = self.session.get(url, timeout=5)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # Game Title
            game_title = title
            h1 = soup.find('h1')
            if h1:
                game_title = h1.get_text().strip()
            
            # Release Date
            release_date = "Not Available"
            date_patterns = [
                r'release date:?\s*([^.]+)',
                r'launch(?:es)?:?\s*([^.]+)',
                r'out now:?\s*([^.]+)'
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
            
            # Key Features
            features = []
            paragraphs = soup.find_all('p')[:3]
            for p in paragraphs:
                p_text = p.get_text().strip()
                if len(p_text) > 30:
                    features.append(p_text[:150] + "..." if len(p_text) > 150 else p_text)
            if not features:
                features = ["Not Available"]
            
            return {
                'game_title': game_title[:100],
                'release_date': release_date,
                'key_features': features[:3],
                'platform_availability': platforms[:3],
                'developer_info': developer,
                'publisher_info': publisher,
                'article_url': url
            }
            
        except Exception as e:
            print(f"Extract error: {e}")
            return None
