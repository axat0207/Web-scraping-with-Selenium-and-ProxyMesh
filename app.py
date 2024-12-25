import os
import json
import time
import logging
from datetime import datetime
from uuid import uuid4
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
from flask import Flask, jsonify, render_template_string

# Set up logging
logging.basicConfig(
    filename='twitter_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Flask app for web interface
app = Flask(__name__)

# Hardcoded credentials
PROXY_HOST = "us-ca.proxymesh.com"
PROXY_PORT = "31280"
PROXY_USERNAME = "axxat"
PROXY_PASSWORD = "Sahilagr@02"
TWITTER_USERNAME = "Axat_02"
TWITTER_PASSWORD = "Sahilagr@02"

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Twitter Trends Scraper</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px;
            background-color: #f5f8fa;
        }
        button { 
            padding: 12px 24px;
            font-size: 16px;
            background-color: #1da1f2;
            color: white;
            border: none;
            border-radius: 24px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #1991da;
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        #results { 
            margin-top: 20px;
            padding: 20px;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        pre {
            background-color: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .error {
            color: #dc3545;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            background-color: #ffe6e6;
        }
    </style>
</head>
<body>
    <button onclick="runScraper()">Click here to run the script</button>
    <div id="results"></div>

    <script>
        function runScraper() {
            const button = document.querySelector('button');
            const resultsDiv = document.getElementById('results');
            
            button.disabled = true;
            button.textContent = 'Scraping...';
            resultsDiv.innerHTML = 'Loading...';
            
            fetch('/scrape')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        resultsDiv.innerHTML = `<div class="error">${data.error}</div>`;
                    } else {
                        resultsDiv.innerHTML = `
                            <h3>These are the most happening topics as on ${data.timestamp}</h3>
                            <ul>
                                ${data.trends.map(trend => `<li>${trend}</li>`).join('')}
                            </ul>
                            <p>The IP address used for this query was ${data.ip_address}</p>
                            <pre>${JSON.stringify(data.mongo_record, null, 2)}</pre>
                        `;
                    }
                })
                .catch(error => {
                    resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
                })
                .finally(() => {
                    button.disabled = false;
                    button.textContent = 'Click here to run the script';
                });
        }
    </script>
</body>
</html>
'''

class TwitterScraper:
    def __init__(self):
        self.mongo_client = MongoClient('mongodb://localhost:27017/')
        self.db = self.mongo_client['stir']
        self.collection = self.db['x']
        logging.info('TwitterScraper initialized with custom database configuration')

    # ... (keep existing setup_driver and login_twitter methods)

    def get_trending_topics(self):
        logging.info('Starting trending topics extraction')
        driver, proxy_ip = self.setup_driver()
        try:
            self.login_twitter(driver)
            
            # Navigate to Twitter home page
            driver.get('https://twitter.com/home')
            time.sleep(5)
            
            # Wait for the "What's happening" section to load
            # The section typically has a heading with "What's happening" text
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//h2[contains(text(), 'What's happening')]"))
            )
            
            # Find the trending topics container
            # Look for the section that comes after the "What's happening" heading
            trending_section = driver.find_element(By.XPATH, "//h2[contains(text(), 'What's happening')]/following-sibling::div")
            
            # Find all trend items
            # Each trend is typically in a cell with role="link"
            trend_elements = trending_section.find_elements(By.CSS_SELECTOR, "[role='link']")
            
            trend_texts = []
            for trend in trend_elements[:5]:  # Get top 5 trends
                try:
                    # Extract the main trend text
                    # Usually the trend name is in a span element
                    trend_text = trend.find_element(By.CSS_SELECTOR, "span").text.strip()
                    
                    # Some trends have additional context (like number of posts)
                    try:
                        trend_context = trend.find_element(By.CSS_SELECTOR, "span[dir='ltr']").text.strip()
                        trend_text = f"{trend_text} ({trend_context})"
                    except:
                        pass
                    
                    if trend_text and trend_text not in trend_texts:
                        trend_texts.append(trend_text)
                        logging.info(f'Found trend: {trend_text}')
                except Exception as e:
                    logging.error(f'Error extracting trend text: {str(e)}')
                    continue
            
            # Create record
            timestamp = datetime.now()
            record = {
                "_id": str(uuid4()),
                "timestamp": timestamp,
                "ip_address": proxy_ip,
                "trends": {f"trend{i+1}": trend for i, trend in enumerate(trend_texts)}
            }
            
            # Save to MongoDB
            self.collection.insert_one(record)
            logging.info(f'Successfully saved trends to MongoDB with ID: {record["_id"]}')
            
            return {
                "trends": trend_texts,
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "ip_address": proxy_ip,
                "mongo_record": record
            }
            
        except Exception as e:
            logging.error(f'Error during scraping: {str(e)}')
            return {"error": str(e)}
        finally:
            driver.quit()
            logging.info('WebDriver closed')
    def __init__(self):
        self.mongo_client = MongoClient('mongodb://localhost:27017/')
        self.db = self.mongo_client['stir']
        self.collection = self.db['x']
        logging.info('TwitterScraper initialized with custom database configuration')

    def setup_driver(self):
        logging.info('Setting up WebDriver')
        options = webdriver.ChromeOptions()
        
        # Configure proxy with authentication
        proxy_string = f"{PROXY_HOST}:{PROXY_PORT}"
        
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Chrome Proxy",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            }
        }
        """

        background_js = """
        var config = {
            mode: "fixed_servers",
            rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: %s
                }
            }
        };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
        );
        """ % (PROXY_HOST, PROXY_PORT, PROXY_USERNAME, PROXY_PASSWORD)

        plugin_dir = 'proxy_auth_plugin'
        if not os.path.exists(plugin_dir):
            os.makedirs(plugin_dir)

        with open(f'{plugin_dir}/manifest.json', 'w') as f:
            f.write(manifest_json)

        with open(f'{plugin_dir}/background.js', 'w') as f:
            f.write(background_js)

        options.add_argument(f'--load-extension={os.path.abspath(plugin_dir)}')
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-notifications')
        
        driver = webdriver.Chrome(options=options)
        logging.info(f'WebDriver setup complete with proxy: {proxy_string}')
        return driver, proxy_string

    def login_twitter(self, driver):
        logging.info('Attempting Twitter login')
        try:
            # Go to Twitter login page
            driver.get('https://twitter.com/login')
            time.sleep(3)
            
            # Enter username
            username_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[autocomplete='username']"))
            )
            username_input.send_keys(TWITTER_USERNAME)
            time.sleep(1)
            
            # Click Next
            next_button = driver.find_element(By.XPATH, "//span[text()='Next']")
            next_button.click()
            time.sleep(2)
            
            # Enter password
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            password_input.send_keys(TWITTER_PASSWORD)
            time.sleep(1)
            
            # Click Login
            login_button = driver.find_element(By.XPATH, "//span[text()='Log in']")
            login_button.click()
            
            # Wait for home page to load
            time.sleep(5)
            logging.info('Successfully logged into Twitter')
            
        except Exception as e:
            logging.error(f'Login failed: {str(e)}')
            raise

    def get_trending_topics(self):
        logging.info('Starting trending topics extraction')
        driver, proxy_ip = self.setup_driver()
        try:
            self.login_twitter(driver)
            
            # Navigate to the explore page
            driver.get('https://twitter.com/')
            time.sleep(5)
            
            # Wait for trends container to be present
            trending_container = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='trend']"))
            )
            
            # Find all trend elements
            trends = driver.find_elements(By.CSS_SELECTOR, "[data-testid='trend']")
            
            # Extract trend texts (up to 5)
            trend_texts = []
            for trend in trends[:5]:
                try:
                    # Get all text elements within the trend
                    trend_elements = trend.find_elements(By.CSS_SELECTOR, "[dir='ltr']")
                    for element in trend_elements:
                        text = element.text.strip()
                        if text and text not in trend_texts:
                            trend_texts.append(text)
                            break  # Take only the first non-empty text from each trend
                    logging.info(f'Found trend: {text}')
                except Exception as e:
                    logging.error(f'Error extracting trend text: {str(e)}')
                    continue
            
            # Create record
            timestamp = datetime.now()
            record = {
                "_id": str(uuid4()),
                "timestamp": timestamp,
                "ip_address": proxy_ip,
                "trends": {f"trend{i+1}": trend for i, trend in enumerate(trend_texts)}
            }
            
            # Save to MongoDB
            self.collection.insert_one(record)
            logging.info(f'Successfully saved trends to MongoDB with ID: {record["_id"]}')
            
            return {
                "trends": trend_texts,
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "ip_address": proxy_ip,
                "mongo_record": record
            }
            
        except Exception as e:
            logging.error(f'Error during scraping: {str(e)}')
            return {"error": str(e)}
        finally:
            driver.quit()
            logging.info('WebDriver closed')

# Flask routes
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/scrape')
def scrape():
    scraper = TwitterScraper()
    result = scraper.get_trending_topics()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)