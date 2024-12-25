import os
import time
import logging
from datetime import datetime
from uuid import uuid4
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    filename='twitter_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TwitterScraper:
    def __init__(self):
        self.mongo_client = MongoClient(os.getenv('MONGO_URI'))
        self.db = self.mongo_client['stir']
        self.collection = self.db['x']
        logging.info('TwitterScraper initialized with custom database configuration')

    def setup_driver(self):
        logging.info('Setting up WebDriver')
        options = webdriver.ChromeOptions()

        # Configure proxy with authentication
        proxy_string = f"{os.getenv('PROXY_HOST')}:{os.getenv('PROXY_PORT')}"
        
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
        """ % (os.getenv('PROXY_HOST'), os.getenv('PROXY_PORT'), os.getenv('PROXY_USERNAME'), os.getenv('PROXY_PASSWORD'))

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
            driver.get('https://twitter.com/login')
            time.sleep(3)
            
            username_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[autocomplete='username']"))
            )
            username_input.send_keys(os.getenv('TWITTER_USERNAME'))
            time.sleep(1)
            
            next_button = driver.find_element(By.XPATH, "//span[text()='Next']")
            next_button.click()
            time.sleep(2)
            
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            password_input.send_keys(os.getenv('TWITTER_PASSWORD'))
            time.sleep(1)
            
            login_button = driver.find_element(By.XPATH, "//span[text()='Log in']")
            login_button.click()
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
            
            driver.get('https://twitter.com/')
            time.sleep(5)
            
            trending_container = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='trend']"))
            )
            
            trends = driver.find_elements(By.CSS_SELECTOR, "[data-testid='trend']")
            
            trend_texts = []
            for trend in trends[:5]:
                try:
                    trend_elements = trend.find_elements(By.CSS_SELECTOR, "[dir='ltr']")
                    for element in trend_elements:
                        text = element.text.strip()
                        if text and text not in trend_texts:
                            trend_texts.append(text)
                            break
                    logging.info(f'Found trend: {text}')
                except Exception as e:
                    logging.error(f'Error extracting trend text: {str(e)}')
                    continue
            
            timestamp = datetime.now()
            record = {
                "_id": str(uuid4()),
                "timestamp": timestamp,
                "ip_address": proxy_ip,
                "trends": {f"trend{i+1}": trend for i, trend in enumerate(trend_texts)}
            }
            
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
