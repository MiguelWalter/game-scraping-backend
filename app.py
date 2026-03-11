from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import GamesRadarScraper
import threading

app = Flask(__name__)
CORS(app)  # This allows your frontend to connect

scraper = GamesRadarScraper()
games_db = []

@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'message': 'GamesRadar Scraper API is running'
    })

@app.route('/api/status')
def get_status():
    return jsonify({'games_count': len(games_db)})

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
    
    print(f"Received scrape request for: {target_url}")
    
    def scrape_task():
        global games_db
        games_db = scraper.scrape_from_url(target_url, count=10)
        print(f"Scrape complete. Found {len(games_db)} games")
    
    thread = threading.Thread(target=scrape_task)
    thread.start()
    
    return jsonify({'message': 'Scraping started'}), 202

# This is required for Vercel
app = app

if __name__ == '__main__':
    app.run(debug=True, port=5000)
