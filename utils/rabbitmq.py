# File: utils/rabbitmq.py
import pika
import json
import time
import socket  

def test_rabbitmq_connection(max_retries=3, retry_delay=2):
    """Test RabbitMQ connection with retries"""
    for attempt in range(max_retries):
        try:
            # Create connection parameters
            parameters = pika.ConnectionParameters(
                host='127.0.0.1',  # Use IP instead of localhost
                port=5672,
                credentials=pika.PlainCredentials('guest', 'guest'),
                connection_attempts=3,
                retry_delay=1,
                socket_timeout=5,
                heartbeat=600
            )
            
            print(f"Attempt {attempt + 1}/{max_retries} - Connecting to RabbitMQ...")
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(queue='device_data')
            connection.close()
            print("RabbitMQ connection successful")
            return True
            
        except Exception as e:
            print(f"RabbitMQ connection attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    return False