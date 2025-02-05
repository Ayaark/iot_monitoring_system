# File: config/config.py

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Global configuration class"""
    
    # Flask configurations
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Database configurations
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'Aftab1999@')
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', '127.0.0.1')
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'iot_db')
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 20,
        'max_overflow': 5
    }

    # RabbitMQ configuration
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', '127.0.0.1')
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', '5672'))
    RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
    RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
    RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', '/')
    RABBITMQ_QUEUE = os.getenv('RABBITMQ_QUEUE', 'device_data')
    
    # Service ports with explicit types
    SIGNING_SERVICE_PORT = int(os.getenv('SIGNING_SERVICE_PORT', '5000'))
    DEVICE_SERVICE_PORT = int(os.getenv('DEVICE_SERVICE_PORT', '5001'))
    MONITORING_SERVICE_PORT = int(os.getenv('MONITORING_SERVICE_PORT', '5002'))

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}