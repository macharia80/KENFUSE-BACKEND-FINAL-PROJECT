from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Memorial, MemorialVisibility, Tribute, User
from datetime import datetime
from . import bp

@bp.route('/memorials', methods=['POST'])
@jwt_required()
def create_memorial():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if user has permission
    user = User.query.get(current_user_id)
    if user.subscription_plan.value == 'free':
        # Check memorial count for free users
        memorial_count = Memorial.query.filter_by(user_id=current_user_id).count()
        if memorial_count >= 1:
            return jsonify({'error': 'Free users are limited to 1 memorial. Upgrade to create more.'}), 403
    
    required_fields = ['deceased_name', 'date_of_birth', 'date_of_passing']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        date_of_passing = datetime.strptime(data['date_of_passing'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    memorial = Memorial(
        user_id=current_user_id,
        deceased_name=data['deceased_name'],
        date_of_birth=date_of_birth,
        date_of_passing=date_of_passing,
        biography=data.get('biography'),
        visibility=MemorialVisibility(data.get('visibility', 'public')),
        location=data.get('location'),
        obituary=data.get('obituary'),
        funeral_details=data.get('funeral_details')
    )
    
    db.session.add(memorial)
    db.session.commit()
    
    return jsonify({
        'message': 'Memorial created successfully',
        'memorial': memorial.to_dict()
    }), 201

@bp.route('/memorials', methods=['GET'])
def get_memorials():
    # Public endpoint - only show public memorials
    visibility = request.args.get('visibility', 'public')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = Memorial.query
    
    if visibility == 'public':
        query = query.filter_by(visibility=MemorialVisibility.PUBLIC)
    
    memorials = query.order_by(Memorial.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'memorials': [memorial.to_dict() for memorial in memorials.items],
        'total': memorials.total,
        'pages': memorials.pages,
        'current_page': page
    }), 200

@bp.route('/memorials/<memorial_id>', methods=['GET'])
def get_memorial(memorial_id):
    memorial = Memorial.query.get(memorial_id)
    
    if not memorial:
        return jsonify({'error': 'Memorial not found'}), 404
    
    # Check visibility
    current_user_id = get_jwt_identity() if request.headers.get('Authorization') else None
    
    if memorial.visibility == MemorialVisibility.PRIVATE:
        if not current_user_id or memorial.user_id != current_user_id:
            return jsonify({'error': 'This memorial is private'}), 403
    elif memorial.visibility == MemorialVisibility.FAMILY_ONLY:
        if not current_user_id:
            return jsonify({'error': 'Authentication required'}), 401
    
    return jsonify({
        'memorial': memorial.to_dict()
    }), 200

@bp.route('/memorials/<memorial_id>/tributes', methods=['POST'])
@jwt_required(optional=True)
def add_tribute(memorial_id):
    memorial = Memorial.query.get(memorial_id)
    
    if not memorial:
        return jsonify({'error': 'Memorial not found'}), 404
    
    data = request.get_json()
    
    if 'message' not in data or 'author_name' not in data:
        return jsonify({'error': 'Message and author name required'}), 400
    
    current_user_id = get_jwt_identity()
    
    tribute = Tribute(
        memorial_id=memorial_id,
        user_id=current_user_id if current_user_id else None,
        message=data['message'],
        author_name=data['author_name'],
        relationship=data.get('relationship'),
        is_anonymous=data.get('is_anonymous', False)
    )
    
    db.session.add(tribute)
    db.session.commit()
    
    return jsonify({
        'message': 'Tribute added successfully',
        'tribute': tribute.to_dict()
    }), 201

@bp.route('/memorials/<memorial_id>/tributes', methods=['GET'])
def get_tributes(memorial_id):
    memorial = Memorial.query.get(memorial_id)
    
    if not memorial:
        return jsonify({'error': 'Memorial not found'}), 404
    
    tributes = Tribute.query.filter_by(memorial_id=memorial_id).order_by(Tribute.created_at.desc()).all()
    
    return jsonify({
        'tributes': [tribute.to_dict() for tribute in tributes]
    }), 200

@bp.route('/memorials/user', methods=['GET'])
@jwt_required()
def get_user_memorials():
    current_user_id = get_jwt_identity()
    
    memorials = Memorial.query.filter_by(user_id=current_user_id).all()
    
    return jsonify({
        'memorials': [memorial.to_dict() for memorial in memorials]
    }), 200

@bp.route('/memorials/<memorial_id>', methods=['PUT'])
@jwt_required()
def update_memorial(memorial_id):
    current_user_id = get_jwt_identity()
    
    memorial = Memorial.query.filter_by(id=memorial_id, user_id=current_user_id).first()
    
    if not memorial:
        return jsonify({'error': 'Memorial not found or unauthorized'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if 'deceased_name' in data:
        memorial.deceased_name = data['deceased_name']
    if 'biography' in data:
        memorial.biography = data['biography']
    if 'visibility' in data:
        try:
            memorial.visibility = MemorialVisibility(data['visibility'])
        except ValueError:
            return jsonify({'error': 'Invalid visibility value'}), 400
    if 'location' in data:
        memorial.location = data['location']
    if 'obituary' in data:
        memorial.obituary = data['obituary']
    if 'funeral_details' in data:
        memorial.funeral_details = data['funeral_details']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Memorial updated successfully',
        'memorial': memorial.to_dict()
    }), 200

@bp.route('/memorials/<memorial_id>', methods=['DELETE'])
@jwt_required()
def delete_memorial(memorial_id):
    current_user_id = get_jwt_identity()
    
    memorial = Memorial.query.filter_by(id=memorial_id, user_id=current_user_id).first()
    
    if not memorial:
        return jsonify({'error': 'Memorial not found or unauthorized'}), 404
    
    db.session.delete(memorial)
    db.session.commit()
    
    return jsonify({
        'message': 'Memorial deleted successfully'
    }), 200
