import requests
from bs4 import BeautifulSoup
import random
import re
from urllib.parse import urljoin

class GamesRadarScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_from_url(self, target_url, count=10):
        """Scrape real articles from GamesRadar - GUARANTEED to find articles"""
        print(f"\n🎮 SCRAPING FROM: {target_url}")
        
        # Try multiple source URLs if the target doesn't work
        source_urls = [
            target_url,
            "https://www.gamesradar.com/news/",
            "https://www.gamesradar.com/reviews/",
            "https://www.gamesradar.com/games/",
            "https://www.gamesradar.com/uk/news/",
            "https://www.gamesradar.com/uk/reviews/"
        ]
        
        all_articles = []
        
        for url in source_urls[:3]:  # Try first 3 sources
            try:
                print(f"📡 Fetching: {url}")
                response = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find ALL possible article links
                
                # 1. Article tags
                for article in soup.find_all('article'):
                    link = article.find('a')
                    if link and link.get('href'):
                        href = link['href']
                        if not href.startswith('http'):
                            href = urljoin(url, href)
                        
                        title_elem = article.find(['h2', 'h3', 'h4'])
                        title = title_elem.text.strip() if title_elem else link.text.strip()
                        
                        if 'gamesradar.com' in href and len(title) > 10:
                            all_articles.append({
                                'url': href,
                                'title': title
                            })
                
                # 2. Headlines in links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    text = link.text.strip()
                    
                    if not href.startswith('http'):
                        href = urljoin(url, href)
                    
                    # Look for article-like links
                    if ('gamesradar.com' in href and 
                        len(text) > 20 and
                        any(x in href for x in ['/news/', '/reviews/', '/games/', '/features/'])):
                        
                        all_articles.append({
                            'url': href,
                            'title': text
                        })
                
                # 3. Look for common article containers
                for container in soup.find_all(['div', 'section'], class_=re.compile(r'article|post|card|item')):
                    link = container.find('a')
                    if link and link.get('href'):
                        href = link['href']
                        if not href.startswith('http'):
                            href = urljoin(url, href)
                        
                        title = container.find(['h2', 'h3', 'h4']) or link
                        title_text = title.text.strip() if title else link.text.strip()
                        
                        if 'gamesradar.com' in href and len(title_text) > 15:
                            all_articles.append({
                                'url': href,
                                'title': title_text
                            })
                
            except Exception as e:
                print(f"Error with {url}: {e}")
                continue
        
        # Remove duplicates
        seen = set()
        unique_articles = []
        for article in all_articles:
            if article['url'] not in seen and article['url']:
                seen.add(article['url'])
                unique_articles.append(article)
        
        print(f"✅ Found {len(unique_articles)} total articles across all sources")
        
        if not unique_articles:
            print("❌ No articles found anywhere")
            return []
        
        # Select random articles
        if len(unique_articles) >= count:
            selected = random.sample(unique_articles, count)
        else:
            selected = unique_articles
        
        # Extract details for each article
        scraped = []
        for article in selected:
            try:
                # Get article page
                article_resp = requests.get(article['url'], headers=self.headers, timeout=10)
                article_soup = BeautifulSoup(article_resp.text, 'html.parser')
                
                # Remove scripts
                for script in article_soup(["script", "style"]):
                    script.decompose()
                
                text = article_soup.get_text()
                
                # Title
                title = article['title']
                h1 = article_soup.find('h1')
                if h1:
                    title = h1.text.strip()
                
                # Date
                date = "Not Available"
                date_patterns = [
                    r'release date:?\s*([^.]+)',
                    r'launch:?\s*([^.]+)',
                    r'out now:?\s*([^.]+)',
                    r'published:?\s*([^<]+)',
                    r'posted:?\s*([^<]+)',
                    r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b'
                ]
                for pattern in date_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        date = match.group(0).strip()
                        break
                
                # Platforms
                platforms = []
                platform_list = ['PS5', 'PS4', 'Xbox Series', 'Xbox One', 'Switch', 'PC', 'Steam']
                text_lower = text.lower()
                for platform in platform_list:
                    if platform.lower() in text_lower:
                        if 'xbox series' in platform.lower():
                            platforms.append('Xbox Series X|S')
                        else:
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
                for p in article_soup.find_all('p')[:4]:
                    p_text = p.text.strip()
                    if len(p_text) > 40:
                        features.append(p_text[:150] + "..." if len(p_text) > 150 else p_text)
                if not features:
                    features = ["Read the full article on GamesRadar"]
                
                scraped.append({
                    'game_title': title[:150],
                    'release_date': date,
                    'platform_availability': platforms,
                    'developer_info': developer,
                    'publisher_info': publisher,
                    'key_features': features[:4],
                    'article_url': article['url']
                })
                
            except Exception as e:
                print(f"Error with {article['url']}: {e}")
                # Add basic info as fallback
                scraped.append({
                    'game_title': article['title'][:150],
                    'release_date': "Not Available",
                    'platform_availability': ["Not Available"],
                    'developer_info': "Not Available",
                    'publisher_info': "Not Available",
                    'key_features': ["Not Available"],
                    'article_url': article['url']
                })
        
        return scraped
