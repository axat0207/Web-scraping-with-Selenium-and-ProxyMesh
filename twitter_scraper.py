from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from uuid import uuid4
import time
import logging
from config import Config
from database import Database
from webdriver_manager import WebDriverManager

class TwitterScraper:
    def __init__(self):
        self.db = Database()
        logging.info('TwitterScraper initialized')

    def login_twitter(self, driver):
        logging.info('Attempting Twitter login')
        try:
            driver.get('https://twitter.com/login')
            time.sleep(3)
            
            username_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[autocomplete='username']"))
            )
            username_input.send_keys(Config.TWITTER_USERNAME)
            time.sleep(1)
            
            next_button = driver.find_element(By.XPATH, "//span[text()='Next']")
            next_button.click()
            time.sleep(2)
            
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
            )
            password_input.send_keys(Config.TWITTER_PASSWORD)
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
        driver, proxy_ip = WebDriverManager.get_driver()
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
            
            self.db.insert_record(record)
            
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