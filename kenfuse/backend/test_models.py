import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing SQLAlchemy models...")

try:
    from app.models import User, Will, Payment
    print("✓ All models imported successfully")
    
    # Check if metadata is a reserved attribute
    import sqlalchemy as sa
    print(f"SQLAlchemy version: {sa.__version__}")
    
    # Test creating a simple instance
    user = User(
        email="test@test.com",
        phone="+254712345678",
        first_name="Test",
        last_name="User"
    )
    user.password = "password123"
    
    print(f"✓ User model test passed: {user.email}")
    
    # Test Payment model
    payment = Payment(
        user_id="test-id",
        amount=100.0,
        payment_method="mpesa"
    )
    print(f"✓ Payment model test passed")
    
    print("\n✅ All model tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
