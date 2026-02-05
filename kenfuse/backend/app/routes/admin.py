from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, UserRole
from . import bp

@bp.route('/dashboard', methods=['GET'])
@jwt_required()
def admin_dashboard():
    current_user_id = get_jwt_identity()
    
    # Check if user is admin
    user = User.query.get(current_user_id)
    if not user or user.role != UserRole.ADMIN:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify({
        'message': 'Admin dashboard endpoint',
        'user': user.to_dict()
    }), 200

@bp.route('/users', methods=['GET'])
@jwt_required()
def get_all_users():
    current_user_id = get_jwt_identity()
    
    # Check if user is admin
    user = User.query.get(current_user_id)
    if not user or user.role != UserRole.ADMIN:
        return jsonify({'error': 'Unauthorized'}), 403
    
    users = User.query.all()
    
    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': len(users)
    }), 200
