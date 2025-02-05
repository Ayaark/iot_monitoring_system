# File: db.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_app_db(app):
    """Initialize database without duplicate registration"""
    if not hasattr(app, '_db_initialized'):
        try:
            db.init_app(app)
            with app.app_context():
                db.create_all()
                print(f"✓ Database initialized for {app.name}")
            app._db_initialized = True
        except Exception as e:
            print(f"Database error: {e}")