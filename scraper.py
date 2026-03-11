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
        """Scrape real articles from GamesRadar"""
        print(f"\n🎮 SCRAPING: {target_url}")
        
        try:
            # Fetch page
            response = requests.get(target_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all article links
            articles = []
            
            # Method 1: Find all article tags
            for article in soup.find_all('article'):
                link = article.find('a')
                if link and link.get('href'):
                    href = link['href']
                    if not href.startswith('http'):
                        href = urljoin(target_url, href)
                    
                    title = article.find(['h2', 'h3', 'h4'])
                    title_text = title.text.strip() if title else link.text.strip()
                    
                    if 'gamesradar.com' in href and len(title_text) > 10:
                        articles.append({
                            'url': href,
                            'title': title_text
                        })
            
            # Method 2: Find links that look like articles
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.text.strip()
                
                if not href.startswith('http'):
                    href = urljoin(target_url, href)
                
                if ('gamesradar.com' in href and 
                    len(text) > 15 and
                    any(x in href for x in ['/news/', '/reviews/', '/games/'])):
                    
                    articles.append({
                        'url': href,
                        'title': text
                    })
            
            # Remove duplicates
            seen = set()
            unique = []
            for a in articles:
                if a['url'] not in seen and a['url']:
                    seen.add(a['url'])
                    unique.append(a)
            
            if not unique:
                return []
            
            # Select random articles
            if len(unique) >= count:
                selected = random.sample(unique, count)
            else:
                selected = unique
            
            # Extract full details for each article
            scraped_games = []
            for article in selected:
                try:
                    # Fetch article page
                    article_response = requests.get(article['url'], headers=self.headers, timeout=10)
                    article_soup = BeautifulSoup(article_response.text, 'html.parser')
                    
                    # Remove scripts
                    for script in article_soup(["script", "style"]):
                        script.decompose()
                    
                    text = article_soup.get_text()
                    
                    # Extract title
                    title = article['title']
                    h1 = article_soup.find('h1')
                    if h1:
                        title = h1.text.strip()
                    
                    # Extract release date
                    date = "Not Available"
                    date_patterns = [
                        r'release date:?\s*([^.]+)',
                        r'launch:?\s*([^.]+)',
                        r'out now:?\s*([^.]+)',
                        r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}\b'
                    ]
                    for pattern in date_patterns:
                        match = re.search(pattern, text, re.IGNORECASE)
                        if match:
                            date = match.group(0).strip()
                            break
                    
                    # Extract platforms
                    platforms = []
                    platform_list = ['PS5', 'PS4', 'Xbox Series X', 'Xbox One', 'Nintendo Switch', 'PC']
                    for platform in platform_list:
                        if platform.lower() in text.lower():
                            platforms.append(platform)
                    if not platforms:
                        platforms = ["Not Available"]
                    
                    # Extract developer
                    developer = "Not Available"
                    dev_match = re.search(r'developer:?\s*([^.]+)', text, re.IGNORECASE)
                    if dev_match:
                        developer = dev_match.group(1).strip()
                    
                    # Extract publisher
                    publisher = "Not Available"
                    pub_match = re.search(r'publisher:?\s*([^.]+)', text, re.IGNORECASE)
                    if pub_match:
                        publisher = pub_match.group(1).strip()
                    
                    # Extract features
                    features = []
                    for p in article_soup.find_all('p')[:5]:
                        p_text = p.text.strip()
                        if len(p_text) > 30:
                            features.append(p_text[:150] + "..." if len(p_text) > 150 else p_text)
                    if not features:
                        features = ["Not Available"]
                    
                    scraped_games.append({
                        'game_title': title[:150],
                        'release_date': date,
                        'platform_availability': platforms,
                        'developer_info': developer,
                        'publisher_info': publisher,
                        'key_features': features[:4],
                        'article_url': article['url']
                    })
                    
                except Exception as e:
                    print(f"Error extracting details: {e}")
                    # Add basic info if detail extraction fails
                    scraped_games.append({
                        'game_title': article['title'][:150],
                        'release_date': "Not Available",
                        'platform_availability': ["Not Available"],
                        'developer_info': "Not Available",
                        'publisher_info': "Not Available",
                        'key_features': ["Not Available"],
                        'article_url': article['url']
                    })
            
            return scraped_games
            
        except Exception as e:
            print(f"Error: {e}")
            return []
