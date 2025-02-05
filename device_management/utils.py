# File: device_management/utils.py
import pika
import json
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def setup_rabbitmq(host='localhost'):
    """Setup RabbitMQ connection and channel"""
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host)
        )
        channel = connection.channel()
        channel.queue_declare(queue='device_data')
        return channel
    except Exception as e:
        print(f"RabbitMQ setup failed: {e}")
        return None

def publish_to_queue(channel, data):
    """Publish data to RabbitMQ queue"""
    try:
        channel.basic_publish(
            exchange='',
            routing_key='device_data',
            body=json.dumps(data)
        )
        return True
    except Exception as e:
        print(f"Failed to publish to queue: {e}")
        return False

def validate_device_data(data):
    """Validate device registration/update data"""
    if not data:
        return False, "No data provided"

    required_fields = ['device_id', 'name']
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"

    if not data['device_id'] or not data['name']:
        return False, "Device ID and name cannot be empty"

    return True, None

def api_response(success=True, message=None, data=None, status_code=200):
    """Generate standardized API response"""
    response = {
        'success': success,
        'message': message,
        'data': data
    }
    return jsonify(response), status_code

def owner_required(f):
    """Decorator to verify device ownership"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        
        # Add device ownership verification logic here
        # This will be implemented in the specific routes
        
        return f(*args, **kwargs)
    return decorated_function