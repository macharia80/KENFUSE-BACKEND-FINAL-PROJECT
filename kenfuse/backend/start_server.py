import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("🚀 Starting KENFUSE Backend Server...")
    print("📡 Server running on: http://localhost:5000")
    print("📊 API Endpoints available at: http://localhost:5000/api")
    print("🔑 Admin: admin@kenfuse.com / Admin@123")
    print("➖" * 50)
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
