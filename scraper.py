import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, urlparse
import random

class GamesRadarScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_from_url(self, target_url, count=10):
        """Scrape random game articles from any GamesRadar URL"""
        print("\n" + "="*60)
        print(f"🎮 SCRAPING FROM: {target_url}")
        print("="*60)
        
        if 'gamesradar.com' not in target_url:
            print("❌ Not a GamesRadar URL")
            return []
        
        try:
            response = requests.get(target_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all article links on the page
            all_articles = []
            
            # Look for article tags
            articles = soup.find_all('article')
            print(f"📊 Found {len(articles)} article elements")
            
            for article in articles:
                link = article.find('a', href=True)
                if link:
                    href = link['href']
                    if not href.startswith('http'):
                        href = urljoin(target_url, href)
                    
                    # Get title
                    title_elem = article.find('h3') or article.find('h2') or article.find('h4')
                    title = title_elem.get_text().strip() if title_elem else link.get_text().strip()
                    
                    if 'gamesradar.com' in href and len(title) > 15:
                        all_articles.append({
                            'url': href,
                            'title': title
                        })
            
            # Also look for links in the page
            for link in soup.find_all('a', href=True):
                href = link['href']
                if not href.startswith('http'):
                    href = urljoin(target_url, href)
                
                text = link.get_text().strip()
                
                if ('gamesradar.com' in href and 
                    len(text) > 20 and
                    any(keyword in href for keyword in ['/news/', '/reviews/', '/games/', '/features/', '/guides/'])):
                    
                    all_articles.append({
                        'url': href,
                        'title': text
                    })
            
            # Remove duplicates
            unique_articles = []
            seen_urls = set()
            for article in all_articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            print(f"✅ Found {len(unique_articles)} unique articles")
            
            if not unique_articles:
                return []
            
            # Select random articles
            if len(unique_articles) >= count:
                selected = random.sample(unique_articles, count)
            else:
                selected = unique_articles
                print(f"⚠️ Only found {len(unique_articles)} articles, using all")
            
            # Extract info from each selected article
            scraped_games = []
            for i, article in enumerate(selected):
                print(f"\n📊 Processing article {i+1}/{len(selected)}")
                game_info = self.extract_game_info(article['url'], article['title'])
                if game_info:
                    scraped_games.append(game_info)
                time.sleep(1)
            
            return scraped_games
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
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
                platforms = ["Not Available"]
            
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
                features = ["Not Available"]
            
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
