from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Fundraiser, FundraiserStatus, Donation, User, Payment, PaymentMethod, PaymentStatus
from datetime import datetime
from . import bp

@bp.route('/fundraisers', methods=['POST'])
@jwt_required()
def create_fundraiser():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if user has permission
    user = User.query.get(current_user_id)
    if user.subscription_plan.value == 'free':
        return jsonify({'error': 'Free users cannot create fundraisers. Upgrade to Standard or Premium.'}), 403
    
    required_fields = ['title', 'description', 'target_amount', 'end_date']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use ISO format'}), 400
    
    if end_date <= datetime.utcnow():
        return jsonify({'error': 'End date must be in the future'}), 400
    
    fundraiser = Fundraiser(
        user_id=current_user_id,
        memorial_id=data.get('memorial_id'),
        title=data['title'],
        description=data['description'],
        target_amount=float(data['target_amount']),
        end_date=end_date,
        currency=data.get('currency', 'KES'),
        cover_image=data.get('cover_image')
    )
    
    db.session.add(fundraiser)
    db.session.commit()
    
    return jsonify({
        'message': 'Fundraiser created successfully',
        'fundraiser': fundraiser.to_dict()
    }), 201

@bp.route('/fundraisers', methods=['GET'])
def get_fundraisers():
    status = request.args.get('status', 'active')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    verified_only = request.args.get('verified', 'true').lower() == 'true'
    
    query = Fundraiser.query
    
    if status != 'all':
        try:
            query = query.filter_by(status=FundraiserStatus(status))
        except ValueError:
            pass
    
    if verified_only:
        query = query.filter_by(is_verified=True)
    
    fundraisers = query.order_by(Fundraiser.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'fundraisers': [fundraiser.to_dict() for fundraiser in fundraisers.items],
        'total': fundraisers.total,
        'pages': fundraisers.pages,
        'current_page': page
    }), 200

@bp.route('/fundraisers/<fundraiser_id>', methods=['GET'])
def get_fundraiser(fundraiser_id):
    fundraiser = Fundraiser.query.get(fundraiser_id)
    
    if not fundraiser:
        return jsonify({'error': 'Fundraiser not found'}), 404
    
    # Get donations for this fundraiser
    donations = Donation.query.filter_by(fundraiser_id=fundraiser_id).order_by(Donation.created_at.desc()).limit(10).all()
    
    response = fundraiser.to_dict()
    response['recent_donations'] = [donation.to_dict() for donation in donations]
    
    return jsonify(response), 200

@bp.route('/fundraisers/<fundraiser_id>/donate', methods=['POST'])
@jwt_required(optional=True)
def donate_to_fundraiser(fundraiser_id):
    fundraiser = Fundraiser.query.get(fundraiser_id)
    
    if not fundraiser:
        return jsonify({'error': 'Fundraiser not found'}), 404
    
    if fundraiser.status != FundraiserStatus.ACTIVE:
        return jsonify({'error': 'This fundraiser is not accepting donations'}), 400
    
    data = request.get_json()
    
    required_fields = ['amount', 'donor_name', 'donor_phone', 'payment_method']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    current_user_id = get_jwt_identity()
    
    # Create donation record
    donation = Donation(
        fundraiser_id=fundraiser_id,
        donor_id=current_user_id,
        amount=float(data['amount']),
        payment_method=data['payment_method'],
        transaction_id=f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        donor_name=data['donor_name'],
        donor_email=data.get('donor_email'),
        donor_phone=data['donor_phone'],
        message=data.get('message'),
        is_anonymous=data.get('is_anonymous', False)
    )
    
    # Create payment record
    payment = Payment(
        user_id=current_user_id if current_user_id else None,
        amount=float(data['amount']),
        payment_method=PaymentMethod(data['payment_method']),
        description=f"Donation to: {fundraiser.title}",
        metadata={
            'fundraiser_id': fundraiser_id,
            'donation_id': donation.id,
            'donor_name': data['donor_name'],
            'donor_phone': data['donor_phone']
        }
    )
    
    db.session.add(donation)
    db.session.add(payment)
    
    # Update fundraiser total
    fundraiser.current_amount += float(data['amount'])
    
    # Check if target reached
    if fundraiser.current_amount >= fundraiser.target_amount:
        fundraiser.status = FundraiserStatus.COMPLETED
    
    db.session.commit()
    
    return jsonify({
        'message': 'Donation initiated successfully',
        'donation': donation.to_dict(),
        'payment': payment.to_dict()
    }), 201

@bp.route('/fundraisers/<fundraiser_id>/donations', methods=['GET'])
def get_fundraiser_donations(fundraiser_id):
    fundraiser = Fundraiser.query.get(fundraiser_id)
    
    if not fundraiser:
        return jsonify({'error': 'Fundraiser not found'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    donations = Donation.query.filter_by(fundraiser_id=fundraiser_id).order_by(Donation.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'donations': [donation.to_dict() for donation in donations.items],
        'total': donations.total,
        'pages': donations.pages,
        'current_page': page
    }), 200

@bp.route('/fundraisers/user', methods=['GET'])
@jwt_required()
def get_user_fundraisers():
    current_user_id = get_jwt_identity()
    
    fundraisers = Fundraiser.query.filter_by(user_id=current_user_id).all()
    
    return jsonify({
        'fundraisers': [fundraiser.to_dict() for fundraiser in fundraisers]
    }), 200

@bp.route('/fundraisers/<fundraiser_id>', methods=['PUT'])
@jwt_required()
def update_fundraiser(fundraiser_id):
    current_user_id = get_jwt_identity()
    
    fundraiser = Fundraiser.query.filter_by(id=fundraiser_id, user_id=current_user_id).first()
    
    if not fundraiser:
        return jsonify({'error': 'Fundraiser not found or unauthorized'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if 'title' in data:
        fundraiser.title = data['title']
    if 'description' in data:
        fundraiser.description = data['description']
    if 'target_amount' in data:
        fundraiser.target_amount = float(data['target_amount'])
    if 'end_date' in data:
        try:
            fundraiser.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    if 'status' in data:
        try:
            fundraiser.status = FundraiserStatus(data['status'])
        except ValueError:
            return jsonify({'error': 'Invalid status'}), 400
    
    db.session.commit()
    
    return jsonify({
        'message': 'Fundraiser updated successfully',
        'fundraiser': fundraiser.to_dict()
    }), 200
