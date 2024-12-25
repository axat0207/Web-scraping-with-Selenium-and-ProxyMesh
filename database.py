from pymongo import MongoClient
from config import Config
import logging

class Database:
    def __init__(self):
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client[Config.MONGO_DB]
        self.collection = self.db[Config.MONGO_COLLECTION]
        logging.info('Database connection initialized')

    def insert_record(self, record):
        try:
            result = self.collection.insert_one(record)
            logging.info(f'Record inserted with ID: {result.inserted_id}')
            return result.inserted_id
        except Exception as e:
            logging.error(f'Error inserting record: {str(e)}')
            raise