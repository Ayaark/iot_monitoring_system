# File: device_management/models.py
from datetime import datetime
from db import db

class Device(db.Model):
    """Device model for storing device information"""
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(120))
    status = db.Column(db.String(20), default='active')
    owner_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime)
    device_type = db.Column(db.String(50))
    device_info = db.Column(db.JSON)
    
    # Define relationship with telemetry
    telemetry = db.relationship('DeviceTelemetry', backref='device', lazy=True)

    def update_last_active(self):
        """Update device's last active timestamp"""
        self.last_active = datetime.utcnow()

    def to_dict(self):
        """Convert device object to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'name': self.name,
            'status': self.status,
            'owner_id': self.owner_id,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'device_type': self.device_type,
            'device_info': self.device_info
        }

class DeviceTelemetry(db.Model):
    """Model for storing device sensor data"""
    __tablename__ = 'device_telemetry'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(80), db.ForeignKey('devices.device_id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    cpu_usage = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    disk_usage = db.Column(db.Float)
    battery_level = db.Column(db.Float)
    signal_strength = db.Column(db.Float)
    raw_data = db.Column(db.JSON)

    def to_dict(self):
        """Convert telemetry record to dictionary"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'timestamp': self.timestamp.isoformat(),
            'temperature': self.temperature,
            'humidity': self.humidity,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'battery_level': self.battery_level,
            'signal_strength': self.signal_strength,
            'raw_data': self.raw_data
        }