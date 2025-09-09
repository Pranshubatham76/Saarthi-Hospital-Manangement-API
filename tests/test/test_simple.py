import sys
import os

# Add the project root directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Disable Redis for testing
os.environ['REDIS_URL'] = ''

from app import create_app
from app.models import db

def test_create_app():
    """Simple test to verify app creation works"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        print("✓ App created successfully")
        print("✓ Database initialized")
        return True

if __name__ == '__main__':
    test_create_app()