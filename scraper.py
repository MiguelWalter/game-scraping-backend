import requests
from bs4 import BeautifulSoup
import time
import re
from urllib.parse import urljoin, urlparse
import random

class GamesRadarScraper:
    def __init__(self):
        self.base_url = "https://www.gamesradar.com/uk/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_homepage_articles(self):
        """Scrape the GamesRadar homepage and extract all article links"""
        print(f"\n📡 Fetching homepage: {self.base_url}")
        
        try:
            response = self.session.get(self.base_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all article links
            article_links = []
            
            # Look for article tags
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
                        article_links.append({
                            'url': full_url,
                            'title': title
                        })
            
            # Also look for links in main content
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().strip()
                
                if href.startswith('http'):
                    full_url = href
                else:
                    full_url = urljoin(self.base_url, href)
                
                # Check if it's a game-related article
                if ('gamesradar.com' in full_url and 
                    len(text) > 20 and
                    any(keyword in full_url for keyword in ['/news/', '/reviews/', '/games/', '/features/', '/guides/'])):
                    
                    article_links.append({
                        'url': full_url,
                        'title': text
                    })
            
            # Remove duplicates
            unique_articles = []
            seen_urls = set()
            for article in article_links:
                if article['url'] not in seen_urls:
                    seen_urls.add(article['url'])
                    unique_articles.append(article)
            
            print(f"✅ Found {len(unique_articles)} unique articles on homepage")
            return unique_articles
            
        except Exception as e:
            print(f"❌ Error fetching homepage: {e}")
            return []
    
    def extract_article_info(self, article_url, article_title):
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
                date = meta_date['content'][:10]  # Get YYYY-MM-DD
            
            # If no meta date, look for date in text
            if date == "Recent":
                date_patterns = [
                    r'published:?\s*([^<]+)',
                    r'posted:?\s*([^<]+)',
                    r'updated:?\s*([^<]+)',
                    r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'
                ]
                for pattern in date_patterns:
                    match = re.search(pattern, text_content, re.IGNORECASE)
                    if match:
                        date = match.group(0)
                        break
            
            # Extract platforms mentioned
            platforms = []
            platform_list = ['PS5', 'PS4', 'PlayStation 5', 'PlayStation 4', 
                           'Xbox Series X', 'Xbox Series S', 'Xbox One', 
                           'Nintendo Switch', 'PC', 'Steam', 'Epic Games']
            
            for platform in platform_list:
                if platform.lower() in text_content.lower():
                    if platform not in platforms:
                        platforms.append(platform)
            
            if not platforms:
                platforms = ["Platform info in article"]
            
            # Extract game name from title or URL
            game_name = title
            # Try to extract a cleaner game name
            game_patterns = [
                r'review:?\s*([^-|]+)',
                r'preview:?\s*([^-|]+)',
                r'guide:?\s*([^-|]+)',
            ]
            for pattern in game_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    game_name = match.group(1).strip()
                    break
            
            # Extract key points from the article
            key_points = []
            
            # Get first few paragraphs
            paragraphs = soup.find_all('p')
            for p in paragraphs[:5]:
                p_text = p.get_text().strip()
                if len(p_text) > 40 and len(p_text) < 250:
                    if not any(skip in p_text.lower() for skip in ['cookie', 'privacy', 'subscribe', 'newsletter']):
                        key_points.append(p_text[:150] + "..." if len(p_text) > 150 else p_text)
            
            if not key_points:
                key_points = ["Click the link to read the full article"]
            
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
                'game_title': game_name[:150],
                'release_date': date[:50],
                'key_features': key_points[:4],
                'platform_availability': platforms[:5],
                'developer_info': "See article for details",
                'publisher_info': "See article for details",
                'article_url': article_url,
                'article_type': article_type
            }
            
        except Exception as e:
            print(f"    ✗ Error extracting data: {e}")
            return None
    
    def scrape_random_articles(self, count=10):
        """Main function to scrape random articles from GamesRadar homepage"""
        print("\n" + "="*70)
        print("🎮 SCRAPING RANDOM ARTICLES FROM GAMESRADAR HOMEPAGE")
        print("="*70)
        
        # Get all articles from homepage
        all_articles = self.get_homepage_articles()
        
        if not all_articles:
            print("❌ No articles found on homepage")
            return []
        
        # Select random articles
        if len(all_articles) >= count:
            selected_articles = random.sample(all_articles, count)
        else:
            selected_articles = all_articles
            print(f"⚠️ Only found {len(all_articles)} articles, using all of them")
        
        print(f"\n🎯 Selected {len(selected_articles)} random articles to scrape")
        
        # Scrape each selected article
        scraped_articles = []
        for i, article in enumerate(selected_articles):
            print(f"\n📊 Article {i+1}/{len(selected_articles)}")
            article_info = self.extract_article_info(article['url'], article['title'])
            
            if article_info:
                scraped_articles.append(article_info)
                print(f"    ✅ Successfully scraped")
            else:
                print(f"    ❌ Failed to scrape")
            
            # Be respectful to the server
            time.sleep(random.uniform(1, 2))
        
        print(f"\n✅ Successfully scraped {len(scraped_articles)} random articles")
        return scraped_articles
