from app.extensions import db
from datetime import datetime
import uuid
import enum

class FundraiserStatus(enum.Enum):
    DRAFT = 'draft'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class Fundraiser(db.Model):
    __tablename__ = 'fundraisers'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    memorial_id = db.Column(db.String(36), db.ForeignKey('memorials.id'), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='KES')
    status = db.Column(db.Enum(FundraiserStatus), default=FundraiserStatus.ACTIVE)
    cover_image = db.Column(db.String(500), nullable=True)
    end_date = db.Column(db.DateTime, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'target_amount': self.target_amount,
            'current_amount': self.current_amount,
            'currency': self.currency,
            'status': self.status.value,
            'cover_image': self.cover_image,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_verified': self.is_verified,
            'progress_percentage': min(100, (self.current_amount / self.target_amount * 100)) if self.target_amount > 0 else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Donation(db.Model):
    __tablename__ = 'donations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fundraiser_id = db.Column(db.String(36), db.ForeignKey('fundraisers.id'), nullable=False)
    donor_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='KES')
    payment_method = db.Column(db.String(20), nullable=False)  # mpesa, card
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    donor_name = db.Column(db.String(100), nullable=False)
    donor_email = db.Column(db.String(120), nullable=True)
    donor_phone = db.Column(db.String(20), nullable=False)
    message = db.Column(db.Text, nullable=True)
    is_anonymous = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'donor_name': self.donor_name,
            'donor_email': self.donor_email,
            'message': self.message,
            'is_anonymous': self.is_anonymous,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
