from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import bp

@bp.route('/payments/mpesa', methods=['POST'])
@jwt_required()
def initiate_mpesa_payment():
    current_user_id = get_jwt_identity()
    
    return jsonify({
        'message': 'M-Pesa payment endpoint',
        'user_id': current_user_id
    }), 200

@bp.route('/payments/card', methods=['POST'])
@jwt_required()
def initiate_card_payment():
    current_user_id = get_jwt_identity()
    
    return jsonify({
        'message': 'Card payment endpoint',
        'user_id': current_user_id
    }), 200
