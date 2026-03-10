import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin
import random

class GamesRadarScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_from_url(self, target_url, count=10):
        """Scrape random game articles from any GamesRadar URL"""
        print("\n" + "="*70)
        print(f"🎮 SCRAPING FROM: {target_url}")
        print("="*70)
        
        # Clean the URL
        base_url = target_url.split('?')[0]
        print(f"📡 Fetching: {base_url}")
        
        try:
            # Get the page
            response = self.session.get(base_url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find ALL article links on the page
            all_articles = []
            
            # Method 1: Look for article tags
            articles = soup.find_all('article')
            print(f"📊 Found {len(articles)} article tags")
            
            for article in articles:
                link = article.find('a', href=True)
                if link:
                    href = link['href']
                    if not href.startswith('http'):
                        href = urljoin(base_url, href)
                    
                    # Get title
                    title_elem = article.find('h3') or article.find('h2') or article.find('h4')
                    title = title_elem.get_text().strip() if title_elem else link.get_text().strip()
                    
                    if 'gamesradar.com' in href and len(title) > 10:
                        all_articles.append({
                            'url': href,
                            'title': title
                        })
                        print(f"  ✅ Found article: {title[:50]}...")
            
            # Method 2: Look for links in the page content
            for link in soup.find_all('a', href=True):
                href = link['href']
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                text = link.get_text().strip()
                
                # Check if it's a game-related article link
                if ('gamesradar.com' in href and 
                    len(text) > 20 and
                    any(keyword in href for keyword in ['/news/', '/reviews/', '/games/', '/features/', '/guides/'])):
                    
                    # Make sure it's not a duplicate
                    if not any(a['url'] == href for a in all_articles):
                        all_articles.append({
                            'url': href,
                            'title': text
                        })
                        print(f"  ✅ Found link: {text[:50]}...")
            
            # Remove duplicates by URL
            unique_articles = []
            seen_urls = set()
            for article in all_articles:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            print(f"\n✅ Total unique articles found: {len(unique_articles)}")
            
            if not unique_articles:
                print("❌ No articles found on this page")
                return []
            
            # Select random articles
            if len(unique_articles) >= count:
                selected = random.sample(unique_articles, count)
                print(f"🎲 Selected {count} random articles")
            else:
                selected = unique_articles
                print(f"⚠️ Only found {len(unique_articles)} articles, using all")
            
            # Extract info from each selected article
            scraped_games = []
            for i, article in enumerate(selected):
                print(f"\n📊 Processing article {i+1}/{len(selected)}")
                print(f"   URL: {article['url']}")
                game_info = self.extract_game_info(article['url'], article['title'])
                if game_info:
                    scraped_games.append(game_info)
                    print(f"   ✅ Successfully extracted")
                else:
                    print(f"   ❌ Failed to extract")
                time.sleep(1.5)  # Be respectful to the server
            
            return scraped_games
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def extract_game_info(self, url, title):
        """Extract game information from article"""
        try:
            print(f"   📄 Fetching article...")
            response = self.session.get(url, timeout=10)
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
            
            # Try meta tags first
            meta_date = soup.find('meta', {'property': 'article:published_time'})
            if meta_date and meta_date.get('content'):
                release_date = meta_date['content'][:10]
            else:
                # Look for date in text
                date_patterns = [
                    r'release date:?\s*([^.]+)',
                    r'launch(?:es)?:?\s*([^.]+)',
                    r'out now:?\s*([^.]+)',
                    r'published:?\s*([^<]+)',
                    r'posted:?\s*([^<]+)',
                    r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        release_date = match.group(0)
                        break
            
            # Get platforms
            platforms = []
            platform_list = ['PS5', 'PS4', 'PlayStation 5', 'PlayStation 4', 
                           'Xbox Series X', 'Xbox Series S', 'Xbox One', 
                           'Nintendo Switch', 'PC', 'Steam']
            
            for platform in platform_list:
                if platform.lower() in text.lower():
                    if platform not in platforms:
                        # Clean up platform name
                        if 'PlayStation 5' in platform or 'PS5' in platform:
                            platforms.append('PS5')
                        elif 'PlayStation 4' in platform or 'PS4' in platform:
                            platforms.append('PS4')
                        elif 'Xbox Series' in platform:
                            platforms.append('Xbox Series X|S')
                        else:
                            platforms.append(platform)
            
            if not platforms:
                platforms = ["Information not available"]
            
            # Get developer
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
                    break
            
            # Get publisher
            publisher = "Not Available"
            pub_patterns = [
                r'publisher:?\s*([^.]+)',
                r'published by:?\s*([^.]+)'
            ]
            for pattern in pub_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    publisher = match.group(1).strip()
                    break
            
            # Get key features/first few paragraphs
            features = []
            paragraphs = soup.find_all('p')
            for p in paragraphs[:4]:
                p_text = p.get_text().strip()
                if len(p_text) > 40 and len(p_text) < 250:
                    if not any(skip in p_text.lower() for skip in ['cookie', 'privacy', 'subscribe', 'newsletter']):
                        features.append(p_text[:150] + "..." if len(p_text) > 150 else p_text)
            
            if not features:
                features = ["Click the link to read the full article on GamesRadar"]
            
            # Determine article type
            article_type = "Article"
            if '/reviews/' in url:
                article_type = "Review"
            elif '/news/' in url:
                article_type = "News"
            elif '/features/' in url:
                article_type = "Feature"
            elif '/guides/' in url:
                article_type = "Guide"
            elif '/previews/' in url:
                article_type = "Preview"
            
            return {
                'game_title': game_title[:150],
                'release_date': release_date,
                'platform_availability': list(set(platforms))[:5],  # Remove duplicates
                'developer_info': developer,
                'publisher_info': publisher,
                'key_features': features[:3],
                'article_url': url,
                'article_type': article_type
            }
            
        except Exception as e:
            print(f"   ❌ Error extracting: {e}")
            return None
