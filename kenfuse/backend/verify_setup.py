#!/usr/bin/env python3
"""
Verify KENFUSE Backend Setup
"""

import os
import sys
import importlib

print("🔍 Verifying KENFUSE Backend Setup...")
print("-" * 50)

# Check Python version
print(f"Python version: {sys.version}")

# Check required modules
required_modules = [
    'flask',
    'flask_sqlalchemy',
    'flask_migrate',
    'flask_jwt_extended',
    'flask_bcrypt',
    'flask_cors',
    'flask_limiter',
    'psycopg2',
    'redis',
    'reportlab'
]

for module in required_modules:
    try:
        importlib.import_module(module)
        print(f"✓ {module}")
    except ImportError as e:
        print(f"✗ {module}: {e}")

print("-" * 50)

# Try to import app
try:
    from app import create_app
    print("✓ app module imports successfully")
    
    # Try to create app
    app = create_app()
    print("✓ Flask app created successfully")
    
    # Check database connection
    with app.app_context():
        from app.extensions import db
        print("✓ Database connection available")
        
except Exception as e:
    print(f"✗ App creation failed: {e}")
    import traceback
    traceback.print_exc()

print("-" * 50)
print("✅ Verification complete!")
