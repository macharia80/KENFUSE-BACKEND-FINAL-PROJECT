#!/bin/bash

echo "🚀 Starting KENFUSE Backend Setup..."

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Setup PostgreSQL
echo "Setting up PostgreSQL..."
sudo systemctl start postgresql 2>/dev/null || true

# Create database if it doesn't exist
sudo -u postgres psql -c "CREATE DATABASE kenfuse_db;" 2>/dev/null || echo "Database already exists"
sudo -u postgres psql -c "CREATE USER kenfuse WITH PASSWORD 'password';" 2>/dev/null || echo "User already exists"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE kenfuse_db TO kenfuse;" 2>/dev/null || echo "Privileges already granted"
sudo -u postgres psql -c "ALTER DATABASE kenfuse_db OWNER TO kenfuse;" 2>/dev/null || echo "Ownership already set"

# Setup Redis
echo "Setting up Redis..."
sudo systemctl start redis 2>/dev/null || echo "Redis already running"

# Create tables directly (bypassing Flask-Migrate for now)
echo "Creating database tables..."
python -c "
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    # Drop all tables first (for clean setup)
    db.drop_all()
    
    # Create all tables
    db.create_all()
    
    print('✓ Database tables created successfully!')
    
    # Create admin user
    from app.models import User, UserRole
    
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
        print('✓ Admin user created: admin@kenfuse.com')
    else:
        print('✓ Admin user already exists')
"

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the backend:"
echo "1. source venv/bin/activate"
echo "2. export FLASK_APP=run.py"
echo "3. export FLASK_ENV=development"
echo "4. flask run --host=0.0.0.0 --port=5000"
echo ""
echo "📡 API will be available at: http://localhost:5000"
echo "🔑 Admin login: admin@kenfuse.com / Admin@123"
