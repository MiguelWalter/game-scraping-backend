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
    
    def verify_url_works(self, url):
        """Verify that a URL actually exists and returns 200 OK"""
        try:
            response = self.session.head(url, timeout=5, allow_redirects=True)
            return response.status_code == 200
        except:
            return False
    
    def search_game(self, game_name):
        """Search for a specific game on GamesRadar and return ONLY real articles with working links"""
        print(f"\n🔍 Searching GamesRadar for: {game_name}")
        print("="*60)
        
        # Format the search query
        search_query = quote(game_name)
        search_url = f"{self.base_url}/search/?q={search_query}"
        
        try:
            print(f"📡 Fetching search results: {search_url}")
            response = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find ALL article links
            all_links = []
            
            # Look for article tags first
            articles = soup.find_all('article')
            print(f"📊 Found {len(articles)} article elements")
            
            for article in articles:
                link = article.find('a', href=True)
                if link:
                    href = link['href']
                    # Convert to full URL
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = urljoin(self.base_url, href)
                    
                    # Get title
                    title_elem = article.find('h3') or article.find('h2') or article.find('h4')
                    title = title_elem.get_text().strip() if title_elem else link.get_text().strip()
                    
                    if 'gamesradar.com' in full_url and len(title) > 15:
                        all_links.append({
                            'url': full_url,
                            'title': title,
                            'source': 'article'
                        })
            
            # Also look for links in search results
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().strip()
                
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(self.base_url, href)
                
                if 'gamesradar.com' in full_url and len(text) > 20:
                    # Check if it's a game-related article
                    if any(keyword in full_url for keyword in ['/news/', '/reviews/', '/games/', '/features/', '/guides/', '/previews/']):
                        all_links.append({
                            'url': full_url,
                            'title': text,
                            'source': 'link'
                        })
            
            # Remove duplicates
            unique_links = []
            seen_urls = set()
            for link in all_links:
                if link['url'] not in seen_urls:
                    seen_urls.add(link['url'])
                    unique_links.append(link)
            
            print(f"📊 Found {len(unique_links)} unique links to check")
            
            # Filter for game name and verify URLs work
            verified_results = []
            for link in unique_links[:20]:  # Check top 20
                # Check if link mentions the game name
                if (game_name.lower() in link['title'].lower() or 
                    game_name.lower() in link['url'].lower()):
                    
                    print(f"  🔍 Checking: {link['title'][:60]}...")
                    
                    # Verify the URL actually works
                    if self.verify_url_works(link['url']):
                        print(f"    ✅ URL is valid: {link['url']}")
                        verified_results.append({
                            'url': link['url'],
                            'title': link['title']
                        })
                    else:
                        print(f"    ❌ URL does not work")
            
            print(f"\n✅ Found {len(verified_results)} REAL, WORKING articles about {game_name}")
            
            if len(verified_results) == 0:
                print("❌ No real articles found. Try a different game name.")
                print("   Examples: 'Elden Ring', 'Baldur's Gate 3', 'Spider-Man 2'")
            
            return verified_results  # Return ONLY verified real results
            
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return []  # Return empty list on error
    
    def extract_game_info(self, article_url, article_title):
        """Extract game information from a REAL GamesRadar article"""
        try:
            print(f"  📄 Extracting data from: {article_url}")
            
            response = self.session.get(article_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script tags
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text()
            
            # Get the main title from the article
            title = article_title
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text().strip()
            
            # Extract date from the article
            date = "Date not specified"
            
            # Try meta tags first
            meta_date = (soup.find('meta', {'property': 'article:published_time'}) or 
                        soup.find('meta', {'name': 'pubdate'}) or 
                        soup.find('meta', {'name': 'publication_date'}))
            
            if meta_date and meta_date.get('content'):
                date = meta_date['content'][:10]  # Get YYYY-MM-DD
            else:
                # Look for time tag
                time_tag = soup.find('time')
                if time_tag:
                    if time_tag.get('datetime'):
                        date = time_tag['datetime'][:10]
                    else:
                        date = time_tag.get_text().strip()
                else:
                    # Look for date in text
                    date_patterns = [
                        r'published:?\s*([^<]+)',
                        r'posted:?\s*([^<]+)',
                        r'updated:?\s*([^<]+)',
                        r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',
                        r'\b\d{1,2} (January|February|March|April|May|June|July|August|September|October|November|December) \d{4}\b'
                    ]
                    for pattern in date_patterns:
                        match = re.search(pattern, text_content, re.IGNORECASE)
                        if match:
                            date = match.group(0)
                            break
            
            # Extract platforms mentioned in the article
            platforms = []
            platform_list = ['PS5', 'PS4', 'PlayStation 5', 'PlayStation 4', 
                           'Xbox Series X', 'Xbox Series S', 'Xbox One', 
                           'Nintendo Switch', 'PC', 'Steam', 'Epic Games',
                           'PlayStation', 'Xbox', 'Switch']
            
            for platform in platform_list:
                if platform.lower() in text_content.lower():
                    if platform not in platforms:
                        platforms.append(platform)
            
            if not platforms:
                platforms = ["Platform information in article"]
            
            # Extract developer (if mentioned)
            developer = "See article for developer info"
            dev_patterns = [
                r'developer:?\s*([^.<]+)',
                r'developed by:?\s*([^.<]+)',
                r'from\s+([^.<,]+)'
            ]
            for pattern in dev_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    developer = match.group(1).strip()
                    break
            
            # Extract publisher (if mentioned)
            publisher = "See article for publisher info"
            pub_patterns = [
                r'publisher:?\s*([^.<]+)',
                r'published by:?\s*([^.<]+)'
            ]
            for pattern in pub_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    publisher = match.group(1).strip()
                    break
            
            # Extract key points from the article
            key_points = []
            
            # Get first few paragraphs
            paragraphs = soup.find_all('p')
            for p in paragraphs[:5]:
                p_text = p.get_text().strip()
                if len(p_text) > 30 and len(p_text) < 200:
                    if not any(skip in p_text.lower() for skip in ['cookie', 'privacy', 'subscribe', 'newsletter']):
                        key_points.append(p_text[:150] + "..." if len(p_text) > 150 else p_text)
            
            if not key_points:
                key_points = ["Read the full article for details"]
            
            # Determine article type
            article_type = "Article"
            if '/reviews/' in article_url:
                article_type = "Review"
            elif '/news/' in article_url:
                article_type = "News"
            elif '/features/' in article_url:
                article_type = "Feature"
            elif '/guides/' in article_url:
                article_type = "Guide"
            elif '/previews/' in article_url:
                article_type = "Preview"
            
            return {
                'game_title': title[:150],
                'release_date': date[:50],
                'key_features': key_points[:4],
                'platform_availability': platforms[:5],
                'developer_info': developer[:100],
                'publisher_info': publisher[:100],
                'article_url': article_url,  # REAL, WORKING URL
                'article_type': article_type
            }
            
        except Exception as e:
            print(f"    ✗ Error extracting data: {e}")
            return None
    
    def scrape_game_reviews(self, game_name):
        """Main function to scrape REAL reviews for a specific game"""
        print("\n" + "="*70)
        print(f"🎮 SEARCHING FOR REAL ARTICLES ABOUT: {game_name.upper()}")
        print("="*70)
        
        # Search for the game - returns ONLY real, verified results
        search_results = self.search_game(game_name)
        
        if not search_results:
            print(f"\n❌ No real articles found for '{game_name}' on GamesRadar")
            print("   Try searching for a different game or check the spelling.")
            return []  # Return empty list - NO SAMPLE DATA
        
        # Scrape each real result
        scraped_games = []
        print(f"\n📊 Processing {len(search_results)} REAL articles...")
        
        for i, result in enumerate(search_results[:10]):  # Take up to 10 real articles
            print(f"\n📊 Article {i+1}/{min(10, len(search_results))}")
            game_info = self.extract_game_info(result['url'], result['title'])
            
            if game_info:
                scraped_games.append(game_info)
                print(f"    ✅ Successfully extracted data")
            else:
                print(f"    ❌ Failed to extract data")
            
            # Be respectful to the server
            time.sleep(random.uniform(1, 2))
        
        print(f"\n✅ Successfully scraped {len(scraped_games)} REAL articles from GamesRadar")
        
        if len(scraped_games) == 0:
            print("❌ Could not extract data from any articles")
        elif len(scraped_games) < 10:
            print(f"⚠️ Only found {len(scraped_games)} real articles. GamesRadar may have limited coverage for this game.")
        
        return scraped_games  # Return ONLY real articles, NO SAMPLES
