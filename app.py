from flask import Flask, jsonify, render_template
import logging
from twitter_scraper import TwitterScraper

# Set up logging
logging.basicConfig(
    filename='twitter_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scrape')
def scrape():
    scraper = TwitterScraper()
    result = scraper.get_trending_topics()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)

