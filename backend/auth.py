"""
Authentication blueprint and routes
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from backend.services.user_service import UserService

auth_bp = Blueprint('auth', __name__)
user_service = UserService()

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = user_service.authenticate_user(username, password)
    if user:
        login_user(user)
        return jsonify({
            'user': user.to_dict(),
            'message': 'Login successful'
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout endpoint"""
    logout_user()
    return jsonify({'message': 'Logout successful'})

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    data = request.get_json()
    
    try:
        user = user_service.create_user(
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            full_name=data.get('full_name')
        )
        return jsonify({
            'user': user.to_dict(),
            'message': 'Registration successful'
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user info"""
    return jsonify({'user': current_user.to_dict()})