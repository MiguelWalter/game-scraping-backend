from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import GamesRadarScraper
import threading
import time

app = Flask(__name__)
CORS(app)

scraper = GamesRadarScraper()
articles_db = []

@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'message': 'GamesRadar Random Article Scraper',
        'endpoints': {
            'scrape': 'POST /api/scrape-random - Scrape 10 random articles',
            'articles': 'GET /api/articles - Get all scraped articles',
            'status': 'GET /api/status - Check status'
        }
    })

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'articles_count': len(articles_db),
        'status': 'ready' if len(articles_db) > 0 else 'empty'
    })

@app.route('/api/articles', methods=['GET'])
def get_articles():
    return jsonify(articles_db)

@app.route('/api/scrape-random', methods=['POST', 'OPTIONS'])
def scrape_random():
    if request.method == 'OPTIONS':
        return '', 200
    
    def scrape_task():
        global articles_db
        try:
            print("\n🕷️ Starting random article scrape...")
            articles = scraper.scrape_random_articles(count=10)
            
            # Clear and update database
            articles_db.clear()
            articles_db.extend(articles)
            
            print(f"✅ Stored {len(articles)} random articles")
        except Exception as e:
            print(f"❌ Error in scrape task: {e}")
    
    thread = threading.Thread(target=scrape_task)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Scraping random articles...'}), 202

app = app

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎮 GAMESRADAR RANDOM ARTICLE SCRAPER")
    print("="*70)
    print("\n🌐 Server running at: http://localhost:5000")
    print("="*70 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
