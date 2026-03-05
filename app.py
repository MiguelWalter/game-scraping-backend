from flask import Flask, render_template, request, jsonify
from flask_cors import CORS  # <- Added for CORS
from scraper import GamesRadarScraper
from database import DatabaseHandler
import threading
import time
import os

app = Flask(__name__)
CORS(app)  # <- This enables all domains to call your backend

# Initialize database and scraper
db = None
scraper = GamesRadarScraper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/games')
def get_games():
    global db
    search_query = request.args.get('search', '')
    
    try:
        if db is None:
            db = DatabaseHandler()
        
        if search_query:
            games = db.search_games(search_query)
        else:
            games = db.get_all_games()
        
        return jsonify(games)
    except Exception as e:
        print(f"Error getting games: {e}")
        return jsonify([])

@app.route('/api/search-game', methods=['POST'])
def search_game():
    """Search for a specific game on GamesRadar"""
    global db
    data = request.get_json()
    game_name = data.get('game_name', '')
    
    if not game_name:
        return jsonify({'error': 'No game name provided'}), 400
    
    def search_task():
        global db
        with app.app_context():
            try:
                print(f"\n🔍 Searching GamesRadar for: {game_name}")
                
                # Clear old data
                if db is None:
                    db = DatabaseHandler()
                db.clear_all_games()
                
                # Search and scrape - ALWAYS GETS 10 RESULTS
                games = scraper.scrape_game_reviews(game_name)
                
                # Store in database
                for game in games:
                    db.insert_game(game)
                
                print(f"✅ Stored exactly {len(games)} articles about {game_name}")
                
            except Exception as e:
                print(f"❌ Error in search task: {e}")
    
    thread = threading.Thread(target=search_task)
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': f'Searching for {game_name}...'}), 202

@app.route('/api/status')
def get_status():
    global db
    try:
        if db is None:
            db = DatabaseHandler()
        games = db.get_all_games()
        return jsonify({
            'games_count': len(games),
            'status': 'ready' if len(games) > 0 else 'empty'
        })
    except Exception as e:
        print(f"Error getting status: {e}")
        return jsonify({'games_count': 0, 'status': 'error'})

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🎮 GAMESRADAR GAME REVIEW SEARCHER - GUARANTEED 10 RESULTS")
    print("="*70)
    
    # Close any existing connections
    if db:
        db.close()
    
    # Remove database file if it exists
    db_path = 'games_data.db'
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("🗑️ Removed old database file")
        except PermissionError:
            print("⚠️ Could not remove database file")
    
    # Create new database
    print("\n📦 Creating new database...")
    db = DatabaseHandler(db_path)
    
    # Add welcome message
    print("\n🎮 Ready to search! Enter any game name to get 10 results.")
    
    print("\n🌐 Server running at: http://localhost:5000")
    print("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
