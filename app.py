import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/workspaces/slownewsinthai/.secrets/total-pier-425200-f4-a424dd7f6f3a.json'

from flask import Flask, request, jsonify, render_template, url_for, send_file, send_from_directory
from flask_caching import Cache
import time
import logging
import os
import glob
import feedparser
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from automation import AUDIO_DIR, compile_daily_post, text_to_speech, run_daily_automation

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', template_folder='.')
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Try to import Celery, but don't fail if it's not available
try:
    from celery import group
    from celery_worker import process_article
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery is not available. Running in non-distributed mode.")

# Set Google Application Credentials
if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    print(f"Using Google credentials from: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
else:
    print("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/articles')
@cache.cached(timeout=300)
def get_articles():
    articles = fetch_rss_feed()
    print(f"Fetched {len(articles)} articles")  # Add this line
    return jsonify([{'title': article['title'], 'summary': article['summary'], 'content': article['content'], 'link': article['link']} for article in articles[:10]])

@app.route('/process', methods=['POST'])
def process():
    try:
        selected_indices = request.json['articles']
        articles = fetch_rss_feed()
        selected_articles = [{'title': articles[int(i)]['title'], 'summary': articles[int(i)]['summary'], 'content': articles[int(i)]['content'], 'link': articles[int(i)]['link']} for i in selected_indices]

        print(f"Processing {len(selected_articles)} articles")  # Debug print

        processed_articles = []
        errors = []
        for article in selected_articles:
            try:
                processed = process_article(article)
                print(f"Processed article: {processed['translated_title']}")  # Debug print
                processed_articles.append(processed)
            except Exception as e:
                error_msg = f"Error processing article '{article['title']}': {str(e)}"
                print(error_msg)  # Debug print
                errors.append(error_msg)

        if not processed_articles and errors:
            return jsonify({"error": "Errors occurred while processing articles", "details": errors}), 500

        return jsonify({"processed": processed_articles, "errors": errors})
    except Exception as e:
        print(f"Error in /process route: {str(e)}")  # Debug print
        return jsonify({"error": f"Server error: {str(e)}"}), 500

def fetch_rss_feed():
    try:
        feed = feedparser.parse("https://www.bangkokpost.com/rss/data/topstories.xml")
        print(f"Fetched {len(feed.entries)} entries from RSS feed")  # Add this line
        articles = []
        for entry in feed.entries[:10]:  # Limit to 10 articles
            articles.append({
                'title': entry.title,
                'summary': entry.description,  # Use description as summary
                'content': entry.description,  # Use description as content
                'link': entry.link
            })
        return articles
    except Exception as e:
        logger.error(f"Error fetching RSS feed: {str(e)}")
        return []

def fetch_full_article_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    article_body = soup.find('div', class_='articl-content')  # Adjust this selector based on the website's structure
    if article_body:
        paragraphs = article_body.find_all('p')
        content = ' '.join([p.text for p in paragraphs])
        return content[:1000]  # Limit to first 1000 characters (adjust as needed)
    return ""

@app.route('/api/daily-summary')
def get_daily_summary():
    try:
        daily_post, audio_filename, transcript = run_daily_automation()
        print(f"Daily post: {daily_post[:100]}...")  # Print first 100 chars
        print(f"Transcript: {transcript[:100]}...")  # Print first 100 chars
        return jsonify({
            "summary": daily_post,
            "audio_filename": audio_filename,
            "transcript": transcript
        })
    except Exception as e:
        print(f"Error in get_daily_summary: {str(e)}")
        import traceback
        traceback.print_exc()  # This will print the full stack trace
        return jsonify({"error": str(e)}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)

if __name__ == "__main__":
    app.run(debug=True)