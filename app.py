from flask import Flask, jsonify
from flask_cors import CORS
import sys

app = Flask(__name__)
CORS(app)

# Simple in-memory storage
games_db = []

@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'message': 'GamesRadar API is running',
        'python_version': sys.version
    })

@app.route('/api/status')
def get_status():
    return jsonify({'games_count': len(games_db)})

@app.route('/api/games')
def get_games():
    return jsonify(games_db)

@app.route('/api/scrape-url', methods=['POST'])
def scrape_url():
    # Simple test response
    return jsonify({'message': 'Test - scraper disabled for now'}), 202

# This is critical for Vercel
app = app

# This only runs locally
if __name__ == '__main__':
    app.run()
