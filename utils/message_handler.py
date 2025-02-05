# File: utils/message_handler.py
import pika
import json
from config.config import config

class RabbitMQHandler:
    def __init__(self, config_name='default'):
        self.config = config[config_name]
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                username=self.config.RABBITMQ_USER,
                password=self.config.RABBITMQ_PASSWORD
            )
            
            parameters = pika.ConnectionParameters(
                host=self.config.RABBITMQ_HOST,
                port=self.config.RABBITMQ_PORT,
                virtual_host=self.config.RABBITMQ_VHOST,
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.config.RABBITMQ_QUEUE)
            return True
            
        except Exception as e:
            print(f"RabbitMQ connection error: {e}")
            return False

    def publish_message(self, message):
        """Publish message to queue"""
        if not self.connection or self.connection.is_closed:
            if not self.connect():
                return False
                
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=self.config.RABBITMQ_QUEUE,
                body=json.dumps(message)
            )
            return True
        except Exception as e:
            print(f"Failed to publish message: {e}")
            return False

    def close(self):
        """Close RabbitMQ connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()