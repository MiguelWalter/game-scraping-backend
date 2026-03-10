import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import random

class GamesRadarScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_from_url(self, target_url, count=10):
        """Fast scraper - gets articles quickly"""
        print(f"\n🎮 FAST SCRAPING FROM: {target_url}")
        
        # Clean URL
        base_url = target_url.split('?')[0]
        
        try:
            # Quick fetch
            response = self.session.get(base_url, timeout=5)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find ALL links quickly
            all_links = []
            
            # Just grab all article links fast
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text().strip()
                
                if not href.startswith('http'):
                    href = urljoin(base_url, href)
                
                # Quick filter for game articles
                if ('gamesradar.com' in href and 
                    len(text) > 15 and
                    any(x in href for x in ['/news/', '/reviews/', '/games/'])):
                    
                    all_links.append({
                        'url': href,
                        'title': text
                    })
            
            # Remove duplicates
            seen = set()
            unique = []
            for link in all_links:
                if link['url'] not in seen:
                    seen.add(link['url'])
                    unique.append(link)
            
            if not unique:
                return []
            
            # Pick random articles
            if len(unique) >= count:
                selected = random.sample(unique, count)
            else:
                selected = unique
            
            # Quick extract (don't deep scrape)
            games = []
            for article in selected:
                try:
                    # Just get basic info fast
                    games.append({
                        'game_title': article['title'][:100],
                        'release_date': "See article",
                        'platform_availability': ["Check article"],
                        'developer_info': "See article",
                        'publisher_info': "See article",
                        'key_features': ["Read full article on GamesRadar"],
                        'article_url': article['url'],
                        'article_type': 'News' if '/news/' in article['url'] else 'Article'
                    })
                except:
                    continue
            
            return games[:count]
            
        except Exception as e:
            print(f"Error: {e}")
            return []
