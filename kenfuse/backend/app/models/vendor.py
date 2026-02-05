from app.extensions import db
from datetime import datetime
import uuid
import enum

class VendorCategory(enum.Enum):
    FUNERAL_HOME = 'funeral_home'
    CASKET = 'casket'
    FLORIST = 'florist'
    CATERING = 'catering'
    TRANSPORT = 'transport'
    VENUE = 'venue'
    LEGAL = 'legal'
    OTHER = 'other'

class VendorStatus(enum.Enum):
    PENDING = 'pending'
    VERIFIED = 'verified'
    SUSPENDED = 'suspended'
    REJECTED = 'rejected'

class VendorProfile(db.Model):
    __tablename__ = 'vendor_profiles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)
    business_name = db.Column(db.String(200), nullable=False)
    business_registration = db.Column(db.String(100), nullable=False)  # Business registration number
    category = db.Column(db.Enum(VendorCategory), nullable=False)
    description = db.Column(db.Text, nullable=False)
    years_in_operation = db.Column(db.Integer, nullable=False)
    county = db.Column(db.String(100), nullable=False)
    town = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(200), nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)
    cover_image = db.Column(db.String(500), nullable=True)
    status = db.Column(db.Enum(VendorStatus), default=VendorStatus.PENDING)
    is_featured = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0.0)
    review_count = db.Column(db.Integer, default=0)
    commission_rate = db.Column(db.Float, default=0.10)  # Default 10% commission
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'business_name': self.business_name,
            'category': self.category.value,
            'description': self.description,
            'years_in_operation': self.years_in_operation,
            'county': self.county,
            'town': self.town,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'logo_url': self.logo_url,
            'cover_image': self.cover_image,
            'status': self.status.value,
            'is_featured': self.is_featured,
            'rating': self.rating,
            'review_count': self.review_count,
            'commission_rate': self.commission_rate,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class VendorService(db.Model):
    __tablename__ = 'vendor_services'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor_id = db.Column(db.String(36), db.ForeignKey('vendor_profiles.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='KES')
    duration = db.Column(db.String(50), nullable=True)  # e.g., "2 hours", "1 day"
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'currency': self.currency,
            'duration': self.duration,
            'is_available': self.is_available,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class VendorBooking(db.Model):
    __tablename__ = 'vendor_bookings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor_id = db.Column(db.String(36), db.ForeignKey('vendor_profiles.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    service_id = db.Column(db.String(36), db.ForeignKey('vendor_services.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'amount': self.amount,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class VendorReview(db.Model):
    __tablename__ = 'vendor_reviews'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vendor_id = db.Column(db.String(36), db.ForeignKey('vendor_profiles.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
