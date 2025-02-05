# File: monitoring_service/database.py
from pymongo import MongoClient
from datetime import datetime
import urllib.parse

class MongoDatabase:
    def __init__(self, uri, database):
        try:
            # Configure MongoDB client with timeout settings
            self.client = MongoClient(
                uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                retryWrites=True,
                retryReads=True
            )
            self.db = self.client[database]
            self.device_data = self.db.device_data
            
            # Quick connection test
            self.client.admin.command('ping')
            print("MongoDB connection successful")
            
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            # Don't raise error - allow system to run without MongoDB
            self.client = None
            self.db = None
            self.device_data = None

    def store_device_data(self, data):
        """Store device data in MongoDB"""
        if not self.device_data:
            print("MongoDB not available - skipping data storage")
            return None
            
        try:
            if 'timestamp' not in data:
                data['timestamp'] = datetime.utcnow()
            return str(self.device_data.insert_one(data).inserted_id)
        except Exception as e:
            print(f"Error storing device data: {e}")
            return None