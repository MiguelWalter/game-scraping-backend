from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import GamesRadarScraper
import threading
import time

app = Flask(__name__)
CORS(app)

scraper = GamesRadarScraper()
games_db = []
scraping_in_progress = False

@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'message': 'GamesRadar Scraper API',
        'endpoints': {
            'scrape': 'POST /api/scrape-url',
            'status': 'GET /api/status',
            'games': 'GET /api/games'
        }
    })

@app.route('/api/status')
def get_status():
    return jsonify({
        'games_count': len(games_db),
        'scraping': scraping_in_progress
    })

@app.route('/api/games')
def get_games():
    return jsonify(games_db)

@app.route('/api/scrape-url', methods=['POST'])
def scrape_url():
    global scraping_in_progress
    
    data = request.get_json()
    target_url = data.get('url', '')
    
    if not target_url or 'gamesradar.com' not in target_url:
        return jsonify({'error': 'Invalid URL'}), 400
    
    def scrape_task():
        global games_db, scraping_in_progress
        scraping_in_progress = True
        try:
            games_db = scraper.scrape_from_url(target_url, count=10)
        finally:
            scraping_in_progress = False
    
    thread = threading.Thread(target=scrape_task)
    thread.start()
    
    return jsonify({'message': 'Scraping started'}), 202

app = app
