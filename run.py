import os
import sys

# Add the kenfuse/backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kenfuse', 'backend'))

from app import create_app

# Set Flask environment
os.environ.setdefault('FLASK_ENV', 'development')

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
