from flask import Flask, jsonify
from flask_cors import CORS
from scraper import GamesRadarScraper
import threading

app = Flask(__name__)
CORS(app)

scraper = GamesRadarScraper()
games_db = []

@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'message': 'GamesRadar Random Game Scraper'
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

@app.route('/api/scrape-random', methods=['POST'])
def scrape_random():
    def scrape_task():
        global games_db
        print("\n🎲 Starting random game scrape...")
        games = scraper.scrape_random_games(count=10)
        games_db = games
        print(f"✅ Stored {len(games)} random games")
    
    thread = threading.Thread(target=scrape_task)
    thread.start()
    return jsonify({'message': 'Scraping random games...'}), 202

app = app

if __name__ == '__main__':
    app.run()
