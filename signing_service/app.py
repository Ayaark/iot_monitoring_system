# File: signing_service/app.py
from flask import Flask, request
from flask_jwt_extended import JWTManager, create_access_token
from datetime import datetime
import os

from .models import db, User
from .utils import error_response, success_response, validate_user_input
from config.config import config

def create_app(config_name='default'):
    """Create and configure the Flask application"""
    app = Flask(__name__)  
    app.name = 'signing'
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    
    # Routes
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        """Register a new user"""
        data = request.get_json()
        
        # Validate input
        is_valid, message = validate_user_input(data)
        if not is_valid:
            return error_response(message)
        
        # Check if user exists
        if User.query.filter_by(username=data['username']).first():
            return error_response('Username already exists')
        
        try:
            # Create new user
            user = User(
                username=data['username'],
                password=data['password']
            )
            db.session.add(user)
            db.session.commit()
            
            return success_response(
                data=user.to_dict(),
                message='User registered successfully',
                status_code=201
            )
        except Exception as e:
            db.session.rollback()
            return error_response(f'Error creating user: {str(e)}', 500)

    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """Log in a user"""
        data = request.get_json()
        
        # Validate input
        is_valid, message = validate_user_input(data)
        if not is_valid:
            return error_response(message)
        
        # Find and verify user
        user = User.query.filter_by(username=data['username']).first()
        if not user or not user.check_password(data['password']):
            return error_response('Invalid username or password', 401)
        
        try:
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Create access token
            access_token = create_access_token(identity=user.id)
            
            return success_response({
                'access_token': access_token,
                'user': user.to_dict()
            })
        except Exception as e:
            db.session.rollback()
            return error_response(f'Error during login: {str(e)}', 500)

    @app.route('/api/auth/user', methods=['GET'])
    def get_user():
        """Get current user information"""
        try:
            # Get user from token
            user = User.query.get(get_jwt_identity())
            if not user:
                return error_response('User not found', 404)
                
            return success_response(user.to_dict())
        except Exception as e:
            return error_response(f'Error retrieving user: {str(e)}', 500)

    return app

if __name__ == '__main__':
    app = create_app(os.getenv('FLASK_CONFIG', 'default'))
    app.run(port=config['default'].SIGNING_SERVICE_PORT)