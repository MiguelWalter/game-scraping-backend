import sqlite3
import json
from datetime import datetime

class DatabaseHandler:
    def __init__(self, db_name='games_data.db'):
        self.db_name = db_name
        self.conn = None
        self.connect()
        self.create_table()
    
    def connect(self):
        """Create a new database connection"""
        try:
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            print(f"✅ Connected to database: {self.db_name}")
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
    
    def create_table(self):
        """Create table if it doesn't exist"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_title TEXT UNIQUE,
                    release_date TEXT,
                    key_features TEXT,
                    platform_availability TEXT,
                    developer_info TEXT,
                    publisher_info TEXT,
                    article_url TEXT,
                    scraped_date TIMESTAMP
                )
            ''')
            self.conn.commit()
        except Exception as e:
            print(f"Error creating table: {e}")
    
    def insert_game(self, game_data):
        """Insert or replace a game"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO games 
                (game_title, release_date, key_features, platform_availability, 
                 developer_info, publisher_info, article_url, scraped_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                game_data['game_title'],
                game_data['release_date'],
                json.dumps(game_data['key_features']),
                json.dumps(game_data['platform_availability']),
                game_data['developer_info'],
                game_data['publisher_info'],
                game_data.get('article_url', '#'),
                datetime.now()
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting game: {e}")
            return False
    
    def get_all_games(self):
        """Get all games from database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT game_title, release_date, key_features, platform_availability,
                       developer_info, publisher_info, article_url
                FROM games
                ORDER BY release_date DESC
            ''')
            rows = cursor.fetchall()
            
            games = []
            for row in rows:
                games.append({
                    'game_title': row[0],
                    'release_date': row[1] or 'TBA',
                    'key_features': json.loads(row[2]) if row[2] else [],
                    'platform_availability': json.loads(row[3]) if row[3] else [],
                    'developer_info': row[4] or 'TBA',
                    'publisher_info': row[5] or 'TBA',
                    'article_url': row[6] or '#'
                })
            return games
        except Exception as e:
            print(f"Error getting games: {e}")
            return []
    
    def search_games(self, query):
        """Search games by title, developer, or publisher"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT game_title, release_date, key_features, platform_availability,
                       developer_info, publisher_info, article_url
                FROM games
                WHERE game_title LIKE ? OR developer_info LIKE ? OR publisher_info LIKE ?
                ORDER BY release_date DESC
            ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
            
            rows = cursor.fetchall()
            games = []
            for row in rows:
                games.append({
                    'game_title': row[0],
                    'release_date': row[1] or 'TBA',
                    'key_features': json.loads(row[2]) if row[2] else [],
                    'platform_availability': json.loads(row[3]) if row[3] else [],
                    'developer_info': row[4] or 'TBA',
                    'publisher_info': row[5] or 'TBA',
                    'article_url': row[6] or '#'
                })
            return games
        except Exception as e:
            print(f"Error searching games: {e}")
            return []
    
    def clear_all_games(self):
        """Clear all games from database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM games")
            self.conn.commit()
            print("🗑️ Database cleared")
        except Exception as e:
            print(f"Error clearing database: {e}")
    
    def get_game_count(self):
        """Get total number of games"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM games")
            return cursor.fetchone()[0]
        except:
            return 0
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("🔒 Database connection closed")