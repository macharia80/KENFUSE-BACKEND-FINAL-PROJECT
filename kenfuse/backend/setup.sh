#!/bin/bash

echo "Setting up KENFUSE Backend..."

# Activate virtual environment
source venv/bin/activate

# Install PostgreSQL if not installed
if ! command -v psql &> /dev/null; then
    echo "Installing PostgreSQL..."
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib
fi

# Install Redis if not installed
if ! command -v redis-server &> /dev/null; then
    echo "Installing Redis..."
    sudo apt-get install -y redis-server
    sudo systemctl start redis
    sudo systemctl enable redis
fi

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE DATABASE kenfuse_db;" 2>/dev/null || true
sudo -u postgres psql -c "CREATE USER kenfuse WITH PASSWORD 'password';" 2>/dev/null || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE kenfuse_db TO kenfuse;" 2>/dev/null || true
sudo -u postgres psql -c "ALTER DATABASE kenfuse_db OWNER TO kenfuse;" 2>/dev/null || true

# Install Python packages
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Set up database migrations
echo "Setting up database migrations..."
export FLASK_APP=run.py
export FLASK_ENV=development

# Initialize migrations
flask db init 2>/dev/null || echo "Migrations already initialized"

# Create migration
flask db migrate -m "Initial tables" 2>/dev/null || echo "Migration already exists"

# Apply migration
flask db upgrade 2>/dev/null || echo "Migration already applied"

# Create admin user
echo "Creating admin user..."
python -c "
from app import create_app
from app.extensions import db
from app.models import User, UserRole

app = create_app()
with app.app_context():
    admin_email = 'admin@kenfuse.com'
    admin_password = 'Admin@123'
    
    admin = User.query.filter_by(email=admin_email, role=UserRole.ADMIN).first()
    
    if not admin:
        admin = User(
            email=admin_email,
            phone='+254700000000',
            first_name='Admin',
            last_name='Kenfuse',
            role=UserRole.ADMIN,
            is_verified=True,
            is_active=True
        )
        admin.password = admin_password
        db.session.add(admin)
        db.session.commit()
        print(f'Admin user created: {admin_email}')
    else:
        print(f'Admin user already exists: {admin_email}')
"

echo "Setup complete!"
echo ""
echo "To run the backend:"
echo "1. source venv/bin/activate"
echo "2. flask run --host=0.0.0.0 --port=5000"
echo ""
echo "Admin credentials:"
echo "Email: admin@kenfuse.com"
echo "Password: Admin@123"
