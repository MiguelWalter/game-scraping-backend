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
    return jsonify({'status': 'ok', 'message': 'GamesRadar Scraper API'})

@app.route('/api/status')
def get_status():
    return jsonify({'games_count': len(games_db)})

@app.route('/api/games')
def get_games():
    return jsonify(games_db)

@app.route('/api/scrape-url', methods=['POST'])
def scrape_url():
    data = request.get_json()
    # Use provided URL or default to homepage
    target_url = data.get('url', 'https://www.gamesradar.com/')

    def scrape_task():
        global games_db
        games_db = scraper.scrape_games(start_url=target_url, max_games=10)

    thread = threading.Thread(target=scrape_task)
    thread.start()
    return jsonify({'message': f'Scraping started from {target_url}'}), 202

# Required for Vercel
app = app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
