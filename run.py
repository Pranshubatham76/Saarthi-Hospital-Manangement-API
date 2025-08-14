import os
from app import create_app, socketio,db
from app.models import Admin, Users, WardCategory
from app.utils.helpers import hash_password
from app.services.websocket_service import websocket_service

# Create Flask application
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Make database models available in shell context"""
    return {
        'db': db,
        'Users': Users,
        'Admin': Admin,
        'WardCategory': WardCategory
    }

def init_db():
    """Initialize database with default data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create default admin user if it doesn't exist
        admin_username = app.config.get('ADMIN_EMAIL', 'admin')
        admin_password = app.config.get('ADMIN_PASSWORD', 'admin123')
        
        if not Admin.query.filter_by(username=admin_username).first():
            admin = Admin(
                username=admin_username,
                password=hash_password(admin_password),
                role='admin'
            )
            db.session.add(admin)
            print(f"Created default admin user: {admin_username}")
        
        # Create default ward categories
        default_categories = [
            {'name': 'General', 'description': 'General ward for regular patients'},
            {'name': 'ICU', 'description': 'Intensive Care Unit'},
            {'name': 'CCU', 'description': 'Cardiac Care Unit'},
            {'name': 'Maternity', 'description': 'Maternity ward'},
            {'name': 'Pediatric', 'description': 'Children\'s ward'},
            {'name': 'Emergency', 'description': 'Emergency department beds'},
            {'name': 'Surgery', 'description': 'Post-surgical recovery beds'}
        ]
        
        for cat_data in default_categories:
            if not WardCategory.query.filter_by(name=cat_data['name']).first():
                category = WardCategory(
                    name=cat_data['name'],
                    description=cat_data['description']
                )
                db.session.add(category)
                print(f"Created ward category: {cat_data['name']}")
        
        # Commit all changes
        db.session.commit()
        print("Database initialization completed!")

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Start background WebSocket tasks
    websocket_service.start_background_tasks()
    
    # Run the application with WebSocket support
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🏥 Hospital Management System API starting on port {port}")
    print(f"📊 API Features enabled:")
    print(f"   ✅ RESTful API with JWT Authentication")
    print(f"   ✅ Real-time WebSocket notifications")
    print(f"   ✅ Redis caching and rate limiting")
    print(f"   ✅ Email notifications")
    print(f"   ✅ Comprehensive audit logging")
    print(f"   ✅ Advanced reporting and analytics")
    print(f"   ✅ Security monitoring")
    print(f"   ✅ Role-based access control (RBAC)")
    print(f"\n🚀 API available at: http://localhost:{port}")
    print(f"📖 API Documentation: http://localhost:{port}/api/info")
    print(f"💚 Health Check: http://localhost:{port}/health")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True if debug else False
    )
