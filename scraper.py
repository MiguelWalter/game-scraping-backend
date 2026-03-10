import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, quote
import random

class GamesRadarScraper:
    def __init__(self):
        self.base_url = "https://www.gamesradar.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_game(self, game_name):
        """Search for a specific game on GamesRadar"""
        print(f"\n🔍 Searching GamesRadar for: {game_name}")
        
        # Try multiple search approaches
        all_results = []
        
        # Approach 1: Direct search
        search_query = quote(game_name)
        search_url = f"{self.base_url}/search/?q={search_query}"
        all_results.extend(self._fetch_search_results(search_url, game_name))
        
        # Approach 2: Check game directory
        game_url = f"{self.base_url}/games/{game_name.lower().replace(' ', '-')}/"
        all_results.extend(self._fetch_page_links(game_url, game_name))
        
        # Approach 3: Check news section
        news_url = f"{self.base_url}/news/"
        all_results.extend(self._fetch_page_links(news_url, game_name))
        
        # Remove duplicates
        unique_results = []
        seen_urls = set()
        for result in all_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        print(f"\n✅ Found {len(unique_results)} articles about {game_name}")
        return unique_results
    
    def _fetch_search_results(self, url, game_name):
        """Fetch and parse search results"""
        results = []
        try:
            print(f"  📡 Checking: {url}")
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all article links
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().strip()
                
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(self.base_url, href)
                
                if 'gamesradar.com' in full_url and len(text) > 15:
                    # Check if it might be related to the game
                    if (game_name.lower() in text.lower() or 
                        game_name.lower() in full_url.lower() or
                        any(word in text.lower() for word in game_name.lower().split())):
                        results.append({
                            'url': full_url,
                            'title': text
                        })
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        return results
    
    def _fetch_page_links(self, url, game_name):
        """Fetch and parse links from a page"""
        results = []
        try:
            print(f"  📡 Checking: {url}")
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for link in soup.find_all('a', href=True)[:30]:
                href = link['href']
                text = link.get_text().strip()
                
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(self.base_url, href)
                
                if 'gamesradar.com' in full_url and len(text) > 20:
                    # Check if it might be related to the game
                    if (game_name.lower() in text.lower() or 
                        game_name.lower() in full_url.lower() or
                        any(word in text.lower() for word in game_name.lower().split())):
                        results.append({
                            'url': full_url,
                            'title': text
                        })
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        return results
    
    def extract_game_info(self, article_url, article_title):
        """Extract game information from an article"""
        try:
            print(f"  📄 Processing: {article_title[:60]}...")
            
            response = self.session.get(article_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script tags
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text()
            
            # Get the main title
            title = article_title
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text().strip()
            
            # Extract date
            date = "Recent"
            meta_date = soup.find('meta', {'property': 'article:published_time'})
            if meta_date and meta_date.get('content'):
                date = meta_date['content'][:10]
            
            # Extract platforms mentioned
            platforms = []
            platform_list = ['PS5', 'PS4', 'Xbox', 'Switch', 'PC', 'PlayStation', 
                           'Nintendo', 'Steam', 'Epic Games']
            
            for platform in platform_list:
                if platform.lower() in text_content.lower():
                    platforms.append(platform)
            
            if not platforms:
                platforms = ["Multiple platforms"]
            
            # Get key points from the article
            key_points = []
            paragraphs = soup.find_all('p')
            for p in paragraphs[:3]:
                p_text = p.get_text().strip()
                if len(p_text) > 30 and len(p_text) < 200:
                    key_points.append(p_text[:150] + "..." if len(p_text) > 150 else p_text)
            
            if not key_points:
                key_points = ["Read the full article on GamesRadar"]
            
            # Determine article type
            article_type = "Article"
            if 'review' in article_url:
                article_type = "Review"
            elif 'news' in article_url:
                article_type = "News"
            elif 'feature' in article_url:
                article_type = "Feature"
            elif 'guide' in article_url:
                article_type = "Guide"
            
            return {
                'game_title': title[:150],
                'release_date': date,
                'key_features': key_points[:3],
                'platform_availability': platforms[:5],
                'developer_info': "See article for details",
                'publisher_info': "See article for details",
                'article_url': article_url,
                'article_type': article_type
            }
            
        except Exception as e:
            print(f"    ✗ Error: {e}")
            return None
    
    def scrape_game_reviews(self, game_name):
        """Main function to scrape articles for a specific game"""
        print("\n" + "="*70)
        print(f"🎮 SEARCHING FOR ARTICLES ABOUT: {game_name.upper()}")
        print("="*70)
        
        # Search for the game
        search_results = self.search_game(game_name)
        
        if not search_results:
            print(f"\n❌ No articles found for '{game_name}'")
            return []
        
        # Scrape each result
        scraped_games = []
        print(f"\n📊 Processing {len(search_results)} articles...")
        
        for i, result in enumerate(search_results[:10]):
            print(f"\n📊 Article {i+1}/{min(10, len(search_results))}")
            game_info = self.extract_game_info(result['url'], result['title'])
            
            if game_info:
                scraped_games.append(game_info)
            
            time.sleep(1)  # Be respectful
        
        print(f"\n✅ Successfully scraped {len(scraped_games)} articles")
        return scraped_games
