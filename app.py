from flask import Flask, request, render_template_string
from scraper import get_random_articles
import traceback
import sys

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>GamesRadar Scraper</title>
    <meta charset="UTF-8">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        input[type=url] { width: 70%; padding: 8px; }
        button { padding: 8px 15px; }
        .error { color: red; }
        ul { list-style-type: none; padding: 0; }
        li { margin: 10px 0; }
        a { word-break: break-all; }
    </style>
</head>
<body>
    <h1>GamesRadar URL Scraper</h1>
    <p>Paste any GamesRadar link to get 10 random game articles</p>
    <form method="post">
        <input type="url" name="url" placeholder="Enter GamesRadar URL" value="{{ request.form.get('url', '') }}" required>
        <button type="submit">Get 10 Random Articles</button>
    </form>
    {% if articles %}
        <h2>Found {{ articles|length }} articles:</h2>
        <ul>
        {% for article in articles %}
            <li><a href="{{ article }}" target="_blank">{{ article }}</a></li>
        {% endfor %}
        </ul>
    {% elif error %}
        <p class="error">{{ error }}</p>
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
        if not url:
            error = "Please enter a URL."
        else:
            try:
                articles = get_random_articles(url)
                if not articles:
                    error = "No articles found on this page. Try a different GamesRadar URL."
            except Exception as e:
                # Print full traceback to Vercel logs
                print("Exception in / route:", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                error = "An internal error occurred. Please try again later."
    return render_template_string(HTML_TEMPLATE, articles=articles, error=error, request=request)

# For local testing
if __name__ == '__main__':
    app.run(debug=True)
