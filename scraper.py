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
        
        # Clean URL
        base_url = target_url.split('?')[0]
        if 'gamesradar.com' in base_url:
            base_url = 'https://www.gamesradar.com/'
        
        try:
            # Fetch page
            response = self.session.get(base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all article links
            all_articles = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().strip()
                
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                # Filter for game articles
                if ('gamesradar.com' in href and 
                    len(text) > 15 and
                    any(x in href for x in ['/news/', '/reviews/', '/games/', '/features/'])):
                    
                    all_articles.append({
                        'url': href,
                        'title': text
                    })
            
            # Remove duplicates
            seen = set()
            unique_articles = []
            for article in all_articles:
                if article['url'] not in seen:
                    seen.add(article['url'])
                    unique_articles.append(article)
            
            if not unique_articles:
                return []
            
            # Select random articles
            if len(unique_articles) >= count:
                selected = random.sample(unique_articles, count)
            else:
                selected = unique_articles
            
            # Extract ALL required fields from each article
            scraped_games = []
            for article in selected:
                print(f"\n📊 Processing: {article['title'][:50]}...")
                game_info = self.extract_all_fields(article['url'], article['title'])
                if game_info:
                    scraped_games.append(game_info)
                time.sleep(1)  # Be respectful
            
            return scraped_games
            
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def extract_all_fields(self, url, title):
        """Extract ALL required fields from article"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove scripts
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # ===========================================
            # 1. GAME TITLE
            # ===========================================
            game_title = title
            h1 = soup.find('h1')
            if h1:
                game_title = h1.get_text().strip()
            if not game_title or game_title == "":
                game_title = "Not Available"
            
            # ===========================================
            # 2. RELEASE DATE
            # ===========================================
            release_date = "Not Available"
            
            # Try meta tags first
            meta_date = soup.find('meta', {'property': 'article:published_time'})
            if meta_date and meta_date.get('content'):
                release_date = meta_date['content'][:10]
            else:
                # Look for date patterns in text
                date_patterns = [
                    r'release date:?\s*([^.]+)',
                    r'launch(?:es)?:?\s*([^.]+)',
                    r'out now:?\s*([^.]+)',
                    r'coming:?\s*([^.]+)',
                    r'published:?\s*([^<]+)',
                    r'posted:?\s*([^<]+)',
                    r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b',
                    r'\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        release_date = match.group(0).strip()
                        break
            
            # ===========================================
            # 3. KEY FEATURES
            # ===========================================
            key_features = []
            
            # Look for bullet points or feature lists
            feature_indicators = ['features', 'gameplay', 'key features', 'what to expect', 
                                'highlights', 'including', 'you can']
            
            # Check list items
            for li in soup.find_all('li'):
                li_text = li.get_text().strip()
                if len(li_text) > 15 and len(li_text) < 200:
                    if any(indicator in li_text.lower() for indicator in feature_indicators):
                        key_features.append(li_text)
            
            # Check paragraphs
            if len(key_features) < 3:
                for p in soup.find_all('p')[:5]:
                    p_text = p.get_text().strip()
                    if len(p_text) > 30 and len(p_text) < 250:
                        if any(indicator in p_text.lower() for indicator in feature_indicators):
                            key_features.append(p_text[:150] + "..." if len(p_text) > 150 else p_text)
            
            # If still no features, get first few sentences
            if not key_features:
                sentences = re.split(r'[.!?]+', text)
                for sentence in sentences[:5]:
                    sentence = sentence.strip()
                    if len(sentence) > 30 and len(sentence) < 200:
                        key_features.append(sentence[:150] + "...")
            
            if not key_features:
                key_features = ["Not Available"]
            
            # Limit to 3-4 features
            key_features = key_features[:4]
            
            # ===========================================
            # 4. PLATFORM AVAILABILITY
            # ===========================================
            platforms = []
            platform_list = [
                'PS5', 'PlayStation 5',
                'PS4', 'PlayStation 4',
                'Xbox Series X', 'Xbox Series S', 'Xbox Series X|S',
                'Xbox One',
                'Nintendo Switch', 'Switch',
                'PC', 'Steam', 'Epic Games Store',
                'iOS', 'iPhone', 'Android', 'Mobile'
            ]
            
            text_lower = text.lower()
            for platform in platform_list:
                if platform.lower() in text_lower:
                    # Clean up platform names
                    if 'playstation 5' in platform_lower or 'ps5' in platform_lower:
                        if 'PS5' not in platforms:
                            platforms.append('PS5')
                    elif 'playstation 4' in platform_lower or 'ps4' in platform_lower:
                        if 'PS4' not in platforms:
                            platforms.append('PS4')
                    elif 'xbox series' in platform_lower:
                        if 'Xbox Series X|S' not in platforms:
                            platforms.append('Xbox Series X|S')
                    elif 'xbox one' in platform_lower:
                        if 'Xbox One' not in platforms:
                            platforms.append('Xbox One')
                    elif 'switch' in platform_lower:
                        if 'Nintendo Switch' not in platforms:
                            platforms.append('Nintendo Switch')
                    elif 'pc' in platform_lower or 'steam' in platform_lower:
                        if 'PC' not in platforms:
                            platforms.append('PC')
                    elif 'ios' in platform_lower or 'iphone' in platform_lower:
                        if 'iOS' not in platforms:
                            platforms.append('iOS')
                    elif 'android' in platform_lower:
                        if 'Android' not in platforms:
                            platforms.append('Android')
            
            if not platforms:
                platforms = ["Not Available"]
            
            # ===========================================
            # 5. DEVELOPER INFORMATION
            # ===========================================
            developer = "Not Available"
            dev_patterns = [
                r'developer:?\s*([^.]+)',
                r'developed by:?\s*([^.]+)',
                r'from\s+([^.<,]+)',
                r'created by:?\s*([^.]+)'
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
            
            # ===========================================
            # 6. PUBLISHER INFORMATION
            # ===========================================
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
            
            # ===========================================
            # Return ALL required fields
            # ===========================================
            return {
                'game_title': game_title[:150],
                'release_date': release_date,
                'key_features': key_features,
                'platform_availability': platforms,
                'developer_info': developer,
                'publisher_info': publisher,
                'article_url': url
            }
            
        except Exception as e:
            print(f"Error extracting: {e}")
            return None
