#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
from app import create_app, db
from app.models import Admin, Users, WardCategory
from app.utils.helpers import hash_password

# Create the Flask application
app = create_app()

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

# Initialize database on startup (for production)
if os.environ.get('FLASK_ENV') == 'production':
    init_db()

if __name__ == "__main__":
    app.run()