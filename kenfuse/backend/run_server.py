#!/usr/bin/env python3
"""
KENFUSE Backend Server Runner
"""

import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from app import create_app
    
    # Create Flask app
    app = create_app()
    
    print("\n" + "="*60)
    print("🚀 KENFUSE BACKEND SERVER")
    print("="*60)
    print(f"📡 URL: http://localhost:5000")
    print(f"📊 API: http://localhost:5000/api")
    print(f"🔑 Admin: admin@kenfuse.com / Admin@123")
    print("="*60 + "\n")
    
    # Run the server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )
    
except Exception as e:
    print(f"❌ Error starting server: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Try running: pip install -r requirements.txt")
