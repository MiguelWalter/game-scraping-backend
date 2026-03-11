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
        """Scrape real articles from GamesRadar - NO HARDCODED DATA"""
        print(f"\n🎮 SCRAPING FROM: {target_url}")
        
        # Use the provided URL or fallback to main page
        base_url = target_url if 'gamesradar.com' in target_url else "https://www.gamesradar.com/"
        
        try:
            # Get the page
            print(f"📡 Fetching: {base_url}")
            response = self.session.get(base_url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find ALL article links
            all_articles = []
            
            # Method 1: Find all article tags
            articles = soup.find_all('article')
            print(f"📊 Found {len(articles)} article tags")
            
            for article in articles:
                link = article.find('a')
                if link and link.get('href'):
                    href = link['href']
                    if not href.startswith('http'):
                        href = urljoin(base_url, href)
                    
                    # Get title
                    title_elem = article.find('h3') or article.find('h2') or article.find('h4')
                    title = title_elem.text.strip() if title_elem else link.text.strip()
                    
                    if 'gamesradar.com' in href and len(title) > 10:
                        all_articles.append({
                            'url': href,
                            'title': title
                        })
                        print(f"  ✅ Found article: {title[:50]}...")
            
            # Method 2: Find links that look like articles
            for link in soup.find_all('a', href=True):
                href = link['href']
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                text = link.text.strip()
                
                # Look for article links
                if ('gamesradar.com' in href and 
                    len(text) > 20 and
                    any(x in href for x in ['/news/', '/reviews/', '/games/', '/features/'])):
                    
                    # Check if we already have this URL
                    if not any(a['url'] == href for a in all_articles):
                        all_articles.append({
                            'url': href,
                            'title': text
                        })
                        print(f"  ✅ Found link: {text[:50]}...")
            
            # Remove duplicates
            seen = set()
            unique_articles = []
            for article in all_articles:
                if article['url'] not in seen:
                    seen.add(article['url'])
                    unique_articles.append(article)
            
            print(f"\n✅ Total unique articles found: {len(unique_articles)}")
            
            if len(unique_articles) == 0:
                print("❌ No articles found on this page")
                return []  # Return empty list - NO HARDCODED DATA
            
            # Select random articles
            if len(unique_articles) >= count:
                selected = random.sample(unique_articles, count)
                print(f"🎲 Selected {count} random articles")
            else:
                selected = unique_articles
                print(f"⚠️ Only found {len(unique_articles)} articles")
            
            # Extract detailed info from each article
            scraped_games = []
            for i, article in enumerate(selected):
                print(f"\n📊 Processing article {i+1}/{len(selected)}: {article['title'][:50]}...")
                game_info = self.extract_detailed_info(article['url'], article['title'])
                if game_info:
                    scraped_games.append(game_info)
                    print(f"   ✅ Successfully extracted")
                else:
                    print(f"   ❌ Failed to extract, using basic info")
                    # Use basic info as fallback for this article only
                    scraped_games.append({
                        'game_title': article['title'][:100],
                        'release_date': 'Not Available',
                        'key_features': ['Information not available in article'],
                        'platform_availability': ['Not Available'],
                        'developer_info': 'Not Available',
                        'publisher_info': 'Not Available',
                        'article_url': article['url']
                    })
                time.sleep(1)  # Be respectful to the server
            
            return scraped_games
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return []  # Return empty list on error - NO HARDCODED DATA
    
    def extract_detailed_info(self, url, title):
        """Extract detailed information from a real article"""
        try:
            # Fetch the article
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # ========== GAME TITLE ==========
            game_title = title
            h1 = soup.find('h1')
            if h1:
                game_title = h1.get_text().strip()
            if not game_title:
                game_title = "Not Available"
            
            # ========== RELEASE DATE ==========
            release_date = "Not Available"
            
            # Try meta tags first
            meta_date = soup.find('meta', {'property': 'article:published_time'})
            if meta_date and meta_date.get('content'):
                release_date = meta_date['content'][:10]
            else:
                # Look for date patterns
                date_patterns = [
                    r'release date:?\s*([^.]+)',
                    r'launch(?:es)?:?\s*([^.]+)',
                    r'out now:?\s*([^.]+)',
                    r'coming:?\s*([^.]+)',
                    r'published:?\s*([^<]+)',
                    r'posted:?\s*([^<]+)',
                    r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        release_date = match.group(0).strip()
                        break
            
            # ========== PLATFORMS ==========
            platforms = []
            platform_list = [
                'PS5', 'PlayStation 5', 
                'PS4', 'PlayStation 4',
                'Xbox Series X', 'Xbox Series S', 'Xbox Series X|S',
                'Xbox One',
                'Nintendo Switch', 'Switch',
                'PC', 'Steam'
            ]
            
            text_lower = text.lower()
            for platform in platform_list:
                if platform.lower() in text_lower:
                    # Clean up platform names
                    if 'playstation 5' in platform.lower() or 'ps5' in platform.lower():
                        if 'PS5' not in platforms:
                            platforms.append('PS5')
                    elif 'playstation 4' in platform.lower() or 'ps4' in platform.lower():
                        if 'PS4' not in platforms:
                            platforms.append('PS4')
                    elif 'xbox series' in platform.lower():
                        if 'Xbox Series X|S' not in platforms:
                            platforms.append('Xbox Series X|S')
                    elif 'xbox one' in platform.lower():
                        if 'Xbox One' not in platforms:
                            platforms.append('Xbox One')
                    elif 'switch' in platform.lower():
                        if 'Nintendo Switch' not in platforms:
                            platforms.append('Nintendo Switch')
                    elif 'pc' in platform.lower() or 'steam' in platform.lower():
                        if 'PC' not in platforms:
                            platforms.append('PC')
            
            if not platforms:
                platforms = ["Not Available"]
            
            # ========== DEVELOPER ==========
            developer = "Not Available"
            dev_patterns = [
                r'developer:?\s*([^.]+)',
                r'developed by:?\s*([^.]+)',
                r'from\s+([^.<,]+)'
            ]
            
            for pattern in dev_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    developer = match.group(1).strip()
                    # Clean up
                    developer = re.sub(r'\s+', ' ', developer)
                    if len(developer) > 50:
                        developer = developer[:50] + "..."
                    break
            
            # ========== PUBLISHER ==========
            publisher = "Not Available"
            pub_patterns = [
                r'publisher:?\s*([^.]+)',
                r'published by:?\s*([^.]+)'
            ]
            
            for pattern in pub_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    publisher = match.group(1).strip()
                    # Clean up
                    publisher = re.sub(r'\s+', ' ', publisher)
                    if len(publisher) > 50:
                        publisher = publisher[:50] + "..."
                    break
            
            # ========== KEY FEATURES ==========
            features = []
            
            # Look for bullet points or feature lists
            for li in soup.find_all('li'):
                li_text = li.get_text().strip()
                if len(li_text) > 20 and len(li_text) < 200:
                    if any(word in li_text.lower() for word in ['feature', 'gameplay', 'includes', 'allows']):
                        features.append(li_text)
            
            # If no list items, look at paragraphs
            if len(features) < 3:
                for p in soup.find_all('p')[:5]:
                    p_text = p.get_text().strip()
                    if len(p_text) > 40 and len(p_text) < 250:
                        if not any(skip in p_text.lower() for skip in ['cookie', 'privacy', 'subscribe']):
                            features.append(p_text[:150] + "..." if len(p_text) > 150 else p_text)
            
            # If still no features, take first few sentences
            if not features:
                sentences = re.split(r'[.!?]+', text)
                for sentence in sentences[:3]:
                    sentence = sentence.strip()
                    if len(sentence) > 30:
                        features.append(sentence[:150] + "...")
            
            if not features:
                features = ["Not Available"]
            
            return {
                'game_title': game_title[:150],
                'release_date': release_date,
                'key_features': features[:4],
                'platform_availability': platforms,
                'developer_info': developer,
                'publisher_info': publisher,
                'article_url': url
            }
            
        except Exception as e:
            print(f"    Error extracting details: {e}")
            return None
