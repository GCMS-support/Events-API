from flask import Blueprint, request, jsonify, current_app
from models import db, User
from flask_jwt_extended import create_access_token


auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    user = User(username=data['username'])
    user.set_password(data['password'])
    
    # First user becomes admin (for demo purposes)
    if current_app.config['FIRST_USER_ADMIN'] and User.query.count() == 0:
        user.is_admin = True
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully', 'user': user.to_dict()}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    access_token = create_access_token(identity=str(user.id), additional_claims={'is_admin': user.is_admin})
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200



