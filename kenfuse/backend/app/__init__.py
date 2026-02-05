from flask import Flask, jsonify
import os
from .config import config
from .extensions import db, migrate, jwt, bcrypt, cors, limiter

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    limiter.init_app(app)
    
    # Register blueprints
    from .routes import bp
    app.register_blueprint(bp, url_prefix='/api')
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # JWT configuration
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        return str(user.id) if hasattr(user, 'id') else user
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        from .models import User
        return User.query.filter_by(id=identity).one_or_none()
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({'error': 'Rate limit exceeded'}), 429
    
    return app

def create_admin_user():
    from .models import User, UserRole
    from .extensions import bcrypt
    
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
        from .extensions import db
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created: {admin_email}")
