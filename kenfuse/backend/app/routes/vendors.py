from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from . import bp

@bp.route('/vendors/register', methods=['POST'])
@jwt_required()
def register_vendor():
    current_user_id = get_jwt_identity()
    
    return jsonify({
        'message': 'Vendor registration endpoint',
        'user_id': current_user_id
    }), 200

@bp.route('/vendors/marketplace', methods=['GET'])
def get_vendors():
    return jsonify({
        'vendors': [],
        'message': 'Vendor marketplace endpoint'
    }), 200
