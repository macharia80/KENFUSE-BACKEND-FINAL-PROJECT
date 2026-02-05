from app.extensions import db
from datetime import datetime
import uuid
import enum

class PaymentStatus(enum.Enum):
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    REFUNDED = 'refunded'

class PaymentMethod(enum.Enum):
    MPESA = 'mpesa'
    CARD = 'card'
    BANK = 'bank'

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='KES')
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = db.Column(db.String(100), unique=True, nullable=True)
    mpesa_receipt = db.Column(db.String(50), nullable=True)
    stripe_payment_intent = db.Column(db.String(100), nullable=True)
    description = db.Column(db.String(500), nullable=True)
    payment_metadata = db.Column(db.JSON, nullable=True)  # Changed from 'metadata' to 'payment_metadata'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method.value,
            'status': self.status.value,
            'transaction_id': self.transaction_id,
            'mpesa_receipt': self.mpesa_receipt,
            'description': self.description,
            'payment_metadata': self.payment_metadata,  # Updated here too
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
