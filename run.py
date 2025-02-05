# File: run.py (in root directory)
import eventlet
eventlet.monkey_patch(socket=True, select=True)

import os
import sys
import time
import socket
import psycopg2
from threading import Thread
from flask import Flask
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from signing_service.app import create_app as create_signing_app
from device_management.app import create_app as create_device_app
from monitoring_service.app import create_app as create_monitoring_app
from virtual_devices.device_simulator import DeviceManager

# Database configuration
DB_CONFIG = {
    'dbname': 'iot_db',
    'user': 'postgres',
    'password': 'Aftab1999@',
    'host': 'localhost',
    'port': '5432'
}

def get_db_connection():
    """Create database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("[OK] Database connected successfully")
        return conn
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return None

def store_device_data(conn, data):
    """Store device data in PostgreSQL"""
    try:
        cur = conn.cursor()
        
        # Check if device exists
        cur.execute(
            "SELECT id FROM devices WHERE device_id = %s",
            (data['device_id'],)
        )
        
        if not cur.fetchone():
            # Create device if not exists
            cur.execute("""
                INSERT INTO devices (device_id, name, owner_id, device_type)
                VALUES (%s, %s, %s, %s)
            """, (
                data['device_id'],
                f"Virtual Device {data['device_id']}",
                1,
                'virtual'
            ))

        # Store telemetry data
        cur.execute("""
            INSERT INTO device_telemetry 
            (device_id, temperature, humidity, cpu_usage, memory_usage, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['device_id'],
            data['temperature'],
            data['humidity'],
            data['cpu_usage'],
            data['memory_usage'],
            datetime.now()
        ))

        # Update device last_active
        cur.execute("""
            UPDATE devices 
            SET last_active = NOW() 
            WHERE device_id = %s
        """, (data['device_id'],))

        conn.commit()
        print(f"[OK] Data stored for device {data['device_id']}")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Error storing data: {e}")

def init_database(app):
    """Initialize database tables within app context"""
    if not hasattr(app, '_db_initialized'):
        try:
            app.config['SQLALCHEMY_DATABASE_URI'] = (
                f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
                f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}"
            )
            app._db_initialized = True
            print(f"[OK] Database initialized for {app.name}")
        except Exception as e:
            print(f"[ERROR] Database error for {app.name}: {e}")

def run_virtual_devices(device_manager, db_conn, interval=5):
    """Run virtual devices simulation"""
    try:
        print("\nStarting virtual devices...")
        threads = []
        for device in device_manager.devices:
            device_thread = Thread(
                target=lambda d=device: device_loop(d, db_conn, interval),
                name=f"device_{device.device_id}",
                daemon=True
            )
            threads.append(device_thread)
            device_thread.start()
            print(f"[OK] Started {device.device_id}")
            
    except Exception as e:
        print(f"[ERROR] Virtual device error: {e}")
        
def device_loop(device, db_conn, interval):
    """Device data generation loop"""
    while True:
        try:
            sensor_data = device.sensor_generator.generate_data()
            data = {
                'device_id': device.device_id,
                'temperature': sensor_data['temperature'],
                'humidity': sensor_data['humidity'],
                'cpu_usage': sensor_data['cpu_usage'],
                'memory_usage': sensor_data['memory_usage'],
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"\nDevice data ({device.device_id}):")
            print(data)
            
            store_device_data(db_conn, data)
            time.sleep(interval)
            
        except Exception as e:
            print(f"[ERROR] Device {device.device_id}: {e}")
            time.sleep(interval)

def start_services(signing_app, device_app, monitoring_app, socketio):
    """Start all microservices"""
    services = [
        Thread(
            target=lambda: signing_app.run(
                host='127.0.0.1', 
                port=5000,
                use_reloader=False
            ),
            name="signing"
        ),
        Thread(
            target=lambda: device_app.run(
                host='127.0.0.1',
                port=5001,
                use_reloader=False
            ),
            name="device"
        ),
        Thread(
            target=lambda: socketio.run(
                monitoring_app,
                host='127.0.0.1',
                port=5002,
                use_reloader=False
            ),
            name="monitoring"
        )
    ]

    print("\nStarting IoT Monitoring System...")
    for service in services:
        print(f"Starting {service.name}...")
        service.daemon = True
        service.start()

def main():
    try:
        # Connect to database
        db_conn = get_db_connection()
        if not db_conn:
            print("[ERROR] Cannot continue without database connection")
            return

        # Create Flask apps
        signing_app = create_signing_app()
        device_app = create_device_app()
        monitoring_app, socketio = create_monitoring_app()

        # Set app names
        signing_app.name = 'signing'
        device_app.name = 'device'
        monitoring_app.name = 'monitoring'

        # Initialize databases
        print("\nInitializing databases...")
        init_database(signing_app)
        init_database(device_app)
        init_database(monitoring_app)

        # Create device manager
        device_manager = DeviceManager(num_devices=3)

        # Start all services
        start_services(signing_app, device_app, monitoring_app, socketio)

        # Wait for services to start
        time.sleep(3)
        
        # Start virtual devices
        run_virtual_devices(device_manager, db_conn)

        print("\n[OK] System started successfully!")
        print("Dashboard: http://127.0.0.1:5002")

        # Monitor system
        while True:
            cur = db_conn.cursor()
            cur.execute("""
                SELECT COUNT(*) FROM device_telemetry 
                WHERE timestamp > NOW() - INTERVAL '1 minute'
            """)
            count = cur.fetchone()[0]
            print(f"[INFO] Last minute: {count} records")
            time.sleep(10)

    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\n[ERROR] Startup error: {e}")
        raise
    finally:
        if 'db_conn' in locals() and db_conn:
            db_conn.close()
            print("[OK] Database connection closed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)