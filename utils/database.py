# File: utils/database.py

import psycopg2
from config.config import Config

def init_db():
    """Initialize database tables"""
    try:
        conn = psycopg2.connect(
            dbname=Config.POSTGRES_DB,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT
        )
        
        with conn.cursor() as cur:
            # Create devices table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id SERIAL PRIMARY KEY,
                    device_id VARCHAR(80) UNIQUE NOT NULL,
                    name VARCHAR(120),
                    status VARCHAR(20) DEFAULT 'active',
                    owner_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP,
                    device_type VARCHAR(50)
                )
            """)
            
            # Create telemetry table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS device_telemetry (
                    id SERIAL PRIMARY KEY,
                    device_id VARCHAR(80) REFERENCES devices(device_id),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    temperature FLOAT,
                    humidity FLOAT,
                    cpu_usage FLOAT,
                    memory_usage FLOAT
                )
            """)
            
        conn.commit()
        print("[OK] Database initialized successfully")
        
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        raise
    finally:
        if conn:
            conn.close()