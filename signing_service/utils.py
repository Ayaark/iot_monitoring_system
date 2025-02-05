# File: signing_service/utils.py
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def error_response(message, status_code=400):
    """Generate standardized error response"""
    response = {
        'error': True,
        'message': message
    }
    return jsonify(response), status_code

def success_response(data=None, message=None, status_code=200):
    """Generate standardized success response"""
    response = {
        'error': False,
        'message': message,
        'data': data
    }
    return jsonify(response), status_code

def validate_user_input(data):
    """Validate user registration/login input"""
    if not data:
        return False, "No data provided"
        
    required_fields = ['username', 'password']
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
            
    username = data['username'].strip()
    password = data['password']
    
    if not username or not password:
        return False, "Username and password cannot be empty"
        
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
        
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    return True, None

def admin_required(fn):
    """Decorator to check if user is admin"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        # Add your admin verification logic here
        # For now, we'll just pass through
        return fn(*args, **kwargs)
    return wrapper