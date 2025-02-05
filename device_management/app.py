# File: device_management/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS  
from datetime import datetime
from device_management.models import db, Device, DeviceTelemetry
from config.config import config

def create_app(config_name='default'):
    """Device management service application factory"""
    app = Flask(__name__)
    CORS(app)  
    
    app.name = 'device'
    app.config.from_object(config[config_name])
    db.init_app(app)

    @app.route('/api/devices', methods=['GET'])
    def get_devices():
        try:
            with app.app_context():
                devices = Device.query.all()
                return jsonify({
                    'success': True,
                    'devices': [device.to_dict() for device in devices]
                })
        except Exception as e:
            print(f"[ERROR] Get devices failed: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return app


    @app.route('/api/devices/<device_id>', methods=['GET'])
    def get_device(device_id):
        """Get specific device details"""
        try:
            device = Device.query.filter_by(device_id=device_id).first()
            if not device:
                return jsonify({
                    'success': False,
                    'error': 'Device not found'
                }), 404

            return jsonify({
                'success': True,
                'device': device.to_dict()
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/device-data', methods=['POST'])
    def receive_data():
        """Store device telemetry data"""
        try:
            data = request.get_json()
            
            if not data or 'device_id' not in data:
                return jsonify({
                    'success': False, 
                    'error': 'Invalid data format'
                }), 400

            # Find or create device
            device = Device.query.filter_by(device_id=data['device_id']).first()
            if not device:
                device = Device(
                    device_id=data['device_id'],
                    name=f"Virtual Device {data['device_id']}",
                    owner_id=1,
                    device_type='virtual'
                )
                db.session.add(device)
            
            # Create telemetry
            telemetry = DeviceTelemetry(
                device_id=data['device_id'],
                temperature=data.get('temperature'),
                humidity=data.get('humidity'),
                cpu_usage=data.get('cpu_usage'),
                memory_usage=data.get('memory_usage')
            )
            
            db.session.add(telemetry)
            device.last_active = datetime.utcnow()
            db.session.commit()
            
            return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] Store telemetry failed: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    return app

    @app.route('/api/device-data/<device_id>', methods=['GET'])
    def get_device_data(device_id):
        """Get device telemetry history"""
        try:
            telemetry = DeviceTelemetry.query\
                .filter_by(device_id=device_id)\
                .order_by(DeviceTelemetry.timestamp.desc())\
                .limit(100)\
                .all()

            return jsonify({
                'success': True,
                'data': [t.to_dict() for t in telemetry]
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return app