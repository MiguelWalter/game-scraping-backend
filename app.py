from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import GamesRadarScraper
from database import DatabaseHandler
import threading
import os

app = Flask(__name__)
CORS(app)

# Initialize database and scraper
db = DatabaseHandler(':memory:')  # Use in-memory database for Vercel
scraper = GamesRadarScraper()

@app.route('/')
def home():
    """Root endpoint - shows API is running"""
    return jsonify({
        'status': 'ok',
        'message': 'GamesRadar API is running',
        'endpoints': {
            'search': 'POST /api/search-game - Search for a game',
            'games': 'GET /api/games - Get all games',
            'status': 'GET /api/status - Check status'
        }
    })

@app.route('/api/games', methods=['GET'])
def get_games():
    """Get all games from database"""
    try:
        search_query = request.args.get('search', '')
        
        if search_query:
            games = db.search_games(search_query)
        else:
            games = db.get_all_games()
        
        return jsonify(games)
    except Exception as e:
        print(f"Error getting games: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-game', methods=['POST', 'OPTIONS'])
def search_game():
    """Search for a game on GamesRadar"""
    # Handle preflight CORS request
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        game_name = data.get('game_name', '')
        
        if not game_name:
            return jsonify({'error': 'No game name provided'}), 400
        
        # Run search in background thread
        def search_task():
            try:
                print(f"\n🔍 Searching for: {game_name}")
                # Clear old data
                db.clear_all_games()
                # Scrape new games
                games = scraper.scrape_game_reviews(game_name)
                
                # Store in database
                for game in games:
                    db.insert_game(game)
                
                print(f"✅ Stored {len(games)} articles about {game_name}")
            except Exception as e:
                print(f"❌ Error in search task: {e}")
        
        # Start background thread
        thread = threading.Thread(target=search_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': f'Searching for {game_name}...',
            'status': 'started'
        }), 202
        
    except Exception as e:
        print(f"Error in search_game: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current status of the database"""
    try:
        games = db.get_all_games()
        return jsonify({
            'games_count': len(games),
            'status': 'ready' if len(games) > 0 else 'empty'
        })
    except Exception as e:
        print(f"Error getting status: {e}")
        return jsonify({
            'games_count': 0,
            'status': 'error',
            'error': str(e)
        }), 500

# This is required for Vercel
app = app

# This only runs when executing locally
if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎮 GAMESRADAR API - LOCAL DEVELOPMENT")
    print("="*70)
    print("\n📡 API Endpoints:")
    print("   GET  /              - API info")
    print("   GET  /api/games     - Get all games")
    print("   POST /api/search-game - Search for a game")
    print("   GET  /api/status    - Check status")
    print("\n🌐 Server running at: http://localhost:5000")
    print("="*70 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
