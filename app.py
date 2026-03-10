from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import GamesRadarScraper
import threading

app = Flask(__name__)
CORS(app)

scraper = GamesRadarScraper()
games_db = []

@app.route('/')
def home():
    return jsonify({'status': 'ok'})

@app.route('/api/status')
def get_status():
    return jsonify({'games_count': len(games_db)})

@app.route('/api/games')
def get_games():
    return jsonify(games_db)

@app.route('/api/scrape-url', methods=['POST'])
def scrape_url():
    def scrape_task():
        global games_db
        games_db = scraper.scrape_from_url("https://www.gamesradar.com/", count=10)
    
    thread = threading.Thread(target=scrape_task)
    thread.start()
    return jsonify({'message': 'Started'}), 202

app = app
