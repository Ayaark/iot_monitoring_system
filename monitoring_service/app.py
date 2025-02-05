# File: monitoring_service/app.py

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO
from flask_cors import CORS  
from sqlalchemy import func
from datetime import datetime, timedelta
import eventlet
import pika
import json

# Import local modules
from db import db
from device_management.models import Device, DeviceTelemetry
from config.config import config

def create_app(config_name='default'):
    """Create and configure monitoring service application"""
    app = Flask(__name__, 
                static_url_path='',
                static_folder='../static')
    
    # Initialize CORS and configs
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.name = 'monitoring'
    app.config.from_object(config[config_name])
    
    # Initialize database
    db.init_app(app)
    
    # Initialize Socket.IO with proper configuration
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=True,
        engineio_logger=True
    )

    def setup_rabbitmq():
        """Setup RabbitMQ connection with retries"""
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            try:
                params = pika.ConnectionParameters(
                    host='127.0.0.1',
                    port=5672,
                    credentials=pika.PlainCredentials('guest', 'guest'),
                    heartbeat=600,
                    connection_attempts=3,
                    retry_delay=2
                )
                connection = pika.BlockingConnection(params)
                channel = connection.channel()
                channel.queue_declare(queue='device_data', durable=True)
                print("[OK] RabbitMQ connected")
                return channel
            except Exception as e:
                print(f"[ERROR] RabbitMQ connection attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2)
        return None

    # Initialize RabbitMQ
    channel = setup_rabbitmq()

    @app.route('/')
    def index():
        """Serve dashboard"""
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/api/devices')
    def get_devices():
        """Get all devices"""
        try:
            with app.app_context():
                devices = Device.query.all()
                device_list = [d.to_dict() for d in devices]
                socketio.emit('devices_update', device_list)
                return jsonify({
                    'success': True,
                    'devices': device_list
                })
        except Exception as e:
            print(f"[ERROR] Failed to fetch devices: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/monitoring/data/<device_id>')
    def get_device_data(device_id):
        """Get device telemetry data"""
        try:
            hours = request.args.get('hours', default=1, type=int)
            start_time = datetime.utcnow() - timedelta(hours=hours)

            telemetry = DeviceTelemetry.query\
                .filter(
                    DeviceTelemetry.device_id == device_id,
                    DeviceTelemetry.timestamp >= start_time
                )\
                .order_by(DeviceTelemetry.timestamp.desc())\
                .all()

            data = [t.to_dict() for t in telemetry]
            socketio.emit(f'device_data_{device_id}', data)
            return jsonify({'success': True, 'data': data})
            
        except Exception as e:
            print(f"[ERROR] Failed to get device data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/monitoring/stats/<device_id>')
    def get_device_stats(device_id):
        """Get device statistics"""
        try:
            hours = request.args.get('hours', default=24, type=int)
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            stats = db.session.query(
                func.avg(DeviceTelemetry.temperature).label('avg_temperature'),
                func.avg(DeviceTelemetry.humidity).label('avg_humidity'),
                func.avg(DeviceTelemetry.cpu_usage).label('avg_cpu'),
                func.min(DeviceTelemetry.temperature).label('min_temperature'),
                func.max(DeviceTelemetry.temperature).label('max_temperature'),
                func.count(DeviceTelemetry.id).label('total_readings')
            ).filter(
                DeviceTelemetry.device_id == device_id,
                DeviceTelemetry.timestamp >= start_time
            ).first()

            return jsonify({
                'success': True,
                'stats': {
                    'avg_temperature': float(stats.avg_temperature or 0),
                    'avg_humidity': float(stats.avg_humidity or 0),
                    'avg_cpu': float(stats.avg_cpu or 0),
                    'min_temperature': float(stats.min_temperature or 0),
                    'max_temperature': float(stats.max_temperature or 0),
                    'total_readings': stats.total_readings or 0,
                    'time_range': f'Last {hours} hours'
                }
            })
            
        except Exception as e:
            print(f"[ERROR] Failed to get device stats: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    def process_device_data(ch, method, properties, body):
        """Process incoming device data from RabbitMQ"""
        try:
            data = json.loads(body)
            socketio.emit(f'device_data_{data["device_id"]}', data)
            print(f"[OK] Processed data for device: {data['device_id']}")
        except Exception as e:
            print(f"[ERROR] Failed to process device data: {e}")

    # Setup RabbitMQ consumer if connection successful
    if channel:
        channel.basic_consume(
            queue='device_data',
            on_message_callback=process_device_data,
            auto_ack=True
        )

    @socketio.on('connect')
    def handle_connect():
        """Handle new WebSocket connection"""
        try:
            print(f"[OK] Client connected: {request.sid}")
            devices = Device.query.all()
            socketio.emit('devices_list', [d.to_dict() for d in devices])
        except Exception as e:
            print(f"[ERROR] Socket connect failed: {e}")

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle WebSocket disconnection"""
        print(f"[INFO] Client disconnected: {request.sid}")

    @socketio.on('subscribe_device')
    def handle_device_subscription(device_id):
        """Handle device data subscription"""
        try:
            print(f"[OK] Client {request.sid} subscribed to device {device_id}")
            get_device_data(device_id)
        except Exception as e:
            print(f"[ERROR] Device subscription failed: {e}")

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'error': 'Not found'}), 404

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({'success': False, 'error': 'Server error'}), 500

    return app, socketio