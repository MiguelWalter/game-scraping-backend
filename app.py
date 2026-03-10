from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import GamesRadarScraper
import threading

app = Flask(__name__)
# Allow all origins for testing
CORS(app, origins=["https://miguelwalter.github.io", "http://localhost:3000", "*"])

scraper = GamesRadarScraper()
games_db = []

@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'message': 'GamesRadar URL Scraper - Paste any GamesRadar link to get 10 random articles'
    })

@app.route('/api/status')
def get_status():
    return jsonify({
        'games_count': len(games_db),
        'status': 'ready' if len(games_db) > 0 else 'empty'
    })

@app.route('/api/games')
def get_games():
    return jsonify(games_db)

@app.route('/api/scrape-url', methods=['POST', 'OPTIONS'])
def scrape_url():
    # Handle preflight CORS request
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response, 200
    
    data = request.get_json()
    target_url = data.get('url', '')
    
    if not target_url:
        return jsonify({'error': 'No URL provided'}), 400
    
    if 'gamesradar.com' not in target_url:
        return jsonify({'error': 'Not a GamesRadar URL'}), 400
    
    def scrape_task():
        global games_db
        print(f"\n🔗 Scraping from URL: {target_url}")
        games = scraper.scrape_from_url(target_url, count=10)
        games_db = games
        print(f"✅ Stored {len(games)} games")
    
    thread = threading.Thread(target=scrape_task)
    thread.start()
    
    return jsonify({'message': f'Scraping from {target_url}...'}), 202

# For Vercel
app = app

if __name__ == '__main__':
    app.run()
