from flask import request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import Will, WillStatus, User
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
from . import bp

@bp.route('/wills', methods=['POST'])
@jwt_required()
def create_will():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check if user has permission
    user = User.query.get(current_user_id)
    if user.subscription_plan.value == 'free':
        # Check will count for free users
        will_count = Will.query.filter_by(user_id=current_user_id).count()
        if will_count >= 1:
            return jsonify({'error': 'Free users are limited to 1 will. Upgrade to create more.'}), 403
    
    required_fields = ['title', 'content', 'beneficiaries']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    will = Will(
        user_id=current_user_id,
        title=data['title'],
        content=data['content'],
        beneficiaries=data['beneficiaries'],
        witnesses=data.get('witnesses'),
        assets=data.get('assets')
    )
    
    db.session.add(will)
    db.session.commit()
    
    return jsonify({
        'message': 'Will created successfully',
        'will': will.to_dict()
    }), 201

@bp.route('/wills', methods=['GET'])
@jwt_required()
def get_wills():
    current_user_id = get_jwt_identity()
    
    wills = Will.query.filter_by(user_id=current_user_id).all()
    
    return jsonify({
        'wills': [will.to_dict() for will in wills]
    }), 200

@bp.route('/wills/<will_id>', methods=['GET'])
@jwt_required()
def get_will(will_id):
    current_user_id = get_jwt_identity()
    
    will = Will.query.filter_by(id=will_id, user_id=current_user_id).first()
    
    if not will:
        return jsonify({'error': 'Will not found'}), 404
    
    return jsonify({
        'will': will.to_dict()
    }), 200

@bp.route('/wills/<will_id>', methods=['PUT'])
@jwt_required()
def update_will(will_id):
    current_user_id = get_jwt_identity()
    
    will = Will.query.filter_by(id=will_id, user_id=current_user_id).first()
    
    if not will:
        return jsonify({'error': 'Will not found'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if 'title' in data:
        will.title = data['title']
    if 'content' in data:
        will.content = data['content']
    if 'beneficiaries' in data:
        will.beneficiaries = data['beneficiaries']
    if 'witnesses' in data:
        will.witnesses = data['witnesses']
    if 'assets' in data:
        will.assets = data['assets']
    if 'status' in data:
        try:
            will.status = WillStatus(data['status'])
        except ValueError:
            return jsonify({'error': 'Invalid status'}), 400
    
    db.session.commit()
    
    return jsonify({
        'message': 'Will updated successfully',
        'will': will.to_dict()
    }), 200

@bp.route('/wills/<will_id>/export-pdf', methods=['GET'])
@jwt_required()
def export_will_pdf(will_id):
    current_user_id = get_jwt_identity()

    will = Will.query.filter_by(id=will_id, user_id=current_user_id).first()

    if not will:
        return jsonify({'error': 'Will not found'}), 404

    # Check if PDF already exists
    pdf_filename = f"will_{will.id}.pdf"
    pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], pdf_filename)

    if os.path.exists(pdf_path):
        # PDF already exists, just return it
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=pdf_filename,
            mimetype='application/pdf'
        )

    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Add content to PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"Last Will and Testament")
    p.drawString(100, 730, f"Title: {will.title}")

    p.setFont("Helvetica", 12)
    p.drawString(100, 700, "This document serves as the last will and testament of:")
    p.drawString(100, 680, f"{will.user.first_name} {will.user.last_name}")

    # Add will content
    text = p.beginText(100, 650)
    text.setFont("Helvetica", 11)
    for line in will.content.split('\n'):
        text.textLine(line[:80])  # Limit line length
    p.drawText(text)

    # Add beneficiaries
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 550, "Beneficiaries:")
    p.setFont("Helvetica", 11)
    y = 530
    for beneficiary in will.beneficiaries:
        p.drawString(120, y, f"- {beneficiary.get('name')}: {beneficiary.get('relationship')}")
        y -= 20

    p.showPage()
    p.save()

    buffer.seek(0)

    # Save PDF to uploads folder
    with open(pdf_path, 'wb') as f:
        f.write(buffer.getvalue())

    # Update will's pdf_url
    will.pdf_url = f"/api/static/uploads/{pdf_filename}"
    db.session.commit()

    return send_file(
        buffer,
        as_attachment=True,
        download_name=pdf_filename,
        mimetype='application/pdf'
    )

@bp.route('/wills/<will_id>', methods=['DELETE'])
@jwt_required()
def delete_will(will_id):
    current_user_id = get_jwt_identity()
    
    will = Will.query.filter_by(id=will_id, user_id=current_user_id).first()
    
    if not will:
        return jsonify({'error': 'Will not found'}), 404
    
    db.session.delete(will)
    db.session.commit()
    
    return jsonify({
        'message': 'Will deleted successfully'
    }), 200
