import os
import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from flask_socketio import SocketIO
from config import config

# Initialize extensions
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()
socketio = SocketIO(cors_allowed_origins="*")


def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV') or 'default'
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    CORS(app)
    
    # Initialize enhanced services
    from app.services.email_service import init_email_service
    from app.services.websocket_service import init_websocket_service
    from app.services.cache_service import init_cache_service
    from app.services.rate_limiter import init_rate_limiter
    
    init_email_service(app)
    init_websocket_service(app, socketio)
    init_cache_service(app)
    init_rate_limiter(app)
    
    # Set up logging
    if not app.debug:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = app.config.get('UPLOAD_FOLDER', 'static/uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        
    # Create logs directory if it doesn't exist
    logs_dir = app.config.get('LOGS_DIR', 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.hospital import hospital_bp
    from app.routes.doctor import doctor_bp
    from app.routes.appointment import appointment_bp
    from app.routes.blood_bank import blood_bank_bp
    from app.routes.emergency import emergency_bp
    from app.routes.admin import admin_bp
    from app.routes.dashboard import dashboard_bp
    # from app.routes.reporting import reporting_bp
    from app.routes.audit import audit_bp
    from app.routes.notifications import notifications_bp
    from app.routes.main import main_bp
    from app.routes.swagger import swagger_bp
    from app.routes.docs import docs_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(hospital_bp, url_prefix='/hospital')
    app.register_blueprint(doctor_bp, url_prefix='/doctor')
    app.register_blueprint(appointment_bp, url_prefix='/appointment')
    app.register_blueprint(blood_bank_bp, url_prefix='/bloodbank')
    app.register_blueprint(emergency_bp, url_prefix='/emergency')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    # app.register_blueprint(reporting_bp, url_prefix='/reporting')  # Temporarily disabled
    app.register_blueprint(audit_bp, url_prefix='/audit')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(main_bp)
    app.register_blueprint(swagger_bp)
    app.register_blueprint(docs_bp)
    
    # JWT configuration
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        # Ensure user identity is always a string
        return str(user)
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        user_type = jwt_data.get('type', 'user')
        
        # Convert identity to int for database lookup
        try:
            user_id = int(identity)
        except (ValueError, TypeError):
            return None
            
        if user_type == 'admin':
            from app.models import Admin
            return Admin.query.get(user_id)
        elif user_type == 'hospital':
            from app.models import Hospital_info
            return Hospital_info.query.get(user_id)
        else:
            from app.models import Users
            return Users.query.get(user_id)
    
    # JWT token handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'message': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'message': 'Invalid token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'message': 'Authorization token required'}, 401
    
    # Error handlers - API only
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Resource not found',
            'error_code': 404
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'error_code': 500
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'message': 'Bad request',
            'error_code': 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'success': False,
            'message': 'Unauthorized access',
            'error_code': 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'success': False,
            'message': 'Forbidden access',
            'error_code': 403
        }), 403
    
    return app
