from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import GamesRadarScraper
import threading

app = Flask(__name__)
CORS(app)

scraper = GamesRadarScraper()
games_db = []  # in-memory storage (can be replaced with JSON/database)

@app.route('/')
def home():
    return jsonify({'status': 'ok', 'message': 'GamesRadar Scraper API'})

@app.route('/api/status')
def get_status():
    return jsonify({'games_count': len(games_db)})

@app.route('/api/games')
def get_games():
    return jsonify(games_db)

@app.route('/api/scrape-url', methods=['POST'])
def scrape_url():
    # We ignore the URL – always scrape from RSS
    def scrape_task():
        global games_db
        games_db = scraper.scrape_from_url(count=10)
    thread = threading.Thread(target=scrape_task)
    thread.start()
    return jsonify({'message': 'Scraping started'}), 202

app = app
