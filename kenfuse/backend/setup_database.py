#!/usr/bin/env python3
"""
Setup KENFUSE Database
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🗄️ Setting up KENFUSE Database...")

try:
    from app import create_app
    from app.extensions import db
    from app.models import User, UserRole
    
    # Create app
    app = create_app()
    
    with app.app_context():
        print("1. Creating database tables...")
        
        # Drop all tables (for clean setup)
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        print("✓ Database tables created")
        
        # Create admin user
        print("2. Creating admin user...")
        admin = User.query.filter_by(email='admin@kenfuse.com').first()
        
        if not admin:
            admin = User(
                email='admin@kenfuse.com',
                phone='+254700000000',
                first_name='Admin',
                last_name='Kenfuse',
                role=UserRole.ADMIN,
                is_verified=True,
                is_active=True
            )
            admin.password = 'Admin@123'
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin user created")
            print(f"   Email: admin@kenfuse.com")
            print(f"   Password: Admin@123")
        else:
            print("✓ Admin user already exists")
        
        # Create test user
        print("3. Creating test user...")
        test_user = User.query.filter_by(email='user@kenfuse.com').first()
        
        if not test_user:
            test_user = User(
                email='user@kenfuse.com',
                phone='+254712345678',
                first_name='John',
                last_name='Doe',
                role=UserRole.FAMILY,
                is_verified=True,
                is_active=True
            )
            test_user.password = 'User@123'
            db.session.add(test_user)
            db.session.commit()
            print("✓ Test user created")
            print(f"   Email: user@kenfuse.com")
            print(f"   Password: User@123")
        
        print("\n✅ Database setup complete!")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
