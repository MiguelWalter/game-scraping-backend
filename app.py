from flask import Flask, request, render_template_string, jsonify
from scraper import get_random_articles
import traceback

app = Flask(__name__)

# Simple HTML form (you can replace with your own template)
HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>GamesRadar Scraper</title>
</head>
<body>
    <h1>GamesRadar URL Scraper</h1>
    <p>Paste any GamesRadar link to get 10 random game articles</p>
    <form method="post">
        <input type="url" name="url" placeholder="Enter GamesRadar URL" required size="50" value="{{ request.form.get('url', '') }}">
        <button type="submit">Get 10 Random Articles</button>
    </form>
    {% if articles %}
        <h2>Results:</h2>
        <ul>
        {% for article in articles %}
            <li><a href="{{ article }}" target="_blank">{{ article }}</a></li>
        {% endfor %}
        </ul>
    {% elif error %}
        <p style="color:red;">{{ error }}</p>
    {% endif %}
    <p><small>Example: https://www.gamesradar.com/uk/ or https://www.gamesradar.com/news/</small></p>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    articles = []
    error = None
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        if url:
            try:
                articles = get_random_articles(url)
                if not articles:
                    error = "No articles found on this page. Try a different GamesRadar URL."
            except Exception as e:
                # Log the error (Vercel will capture this in logs)
                print("Error in / route:", traceback.format_exc())
                error = "An internal error occurred. Please try again later."
        else:
            error = "Please enter a URL."
    return render_template_string(HTML_FORM, articles=articles, error=error)

# This is required for Vercel's serverless function
app.debug = False
