from requests_html import HTMLSession
import time
import random
import re

class GamesRadarScraper:
    def __init__(self):
        self.session = HTMLSession()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_from_url(self, target_url, count=10):
        """Scrape articles using JavaScript rendering"""
        print(f"\n🎮 SCRAPING FROM: {target_url}")
        
        try:
            # Get the page and render JavaScript
            print("📡 Fetching page with JavaScript...")
            response = self.session.get(target_url)
            response.html.render(timeout=20, sleep=2)  # Wait for JS to load
            
            print("✅ Page rendered successfully")
            
            # Find all article links
            all_articles = []
            
            # Look for article links in the rendered content
            links = response.html.find('a')
            print(f"📊 Found {len(links)} total links")
            
            for link in links:
                href = link.attrs.get('href', '')
                text = link.text.strip()
                
                if not href or not text:
                    continue
                    
                if not href.startswith('http'):
                    if href.startswith('/'):
                        href = f"https://www.gamesradar.com{href}"
                    else:
                        continue
                
                # Check if it's a game article
                if ('gamesradar.com' in href and 
                    len(text) > 15 and
                    any(x in href for x in ['/news/', '/reviews/', '/games/', '/features/'])):
                    
                    all_articles.append({
                        'url': href,
                        'title': text
                    })
            
            # Remove duplicates
            unique = []
            seen = set()
            for article in all_articles:
                if article['url'] not in seen:
                    seen.add(article['url'])
                    unique.append(article)
            
            print(f"✅ Found {len(unique)} unique articles")
            
            if not unique:
                print("❌ No articles found")
                return []
            
            # Select random articles
            if len(unique) >= count:
                selected = random.sample(unique, count)
            else:
                selected = unique
            
            # Extract info (simplified for speed)
            games = []
            for article in selected:
                games.append({
                    'game_title': article['title'][:100],
                    'release_date': 'See article',
                    'key_features': ['Read full article for details'],
                    'platform_availability': ['Check article'],
                    'developer_info': 'See article',
                    'publisher_info': 'See article',
                    'article_url': article['url']
                })
            
            return games
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
