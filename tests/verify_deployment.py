#!/usr/bin/env python3
"""
Hospital Management System - Deployment Readiness Verification Script
This script checks if the system is ready for deployment.
"""

import os
import sys
from pathlib import Path

def check_file_exists(file_path, description=""):
    """Check if a file exists"""
    if os.path.exists(file_path):
        size = os.path.getsize(file_path) if os.path.isfile(file_path) else "DIR"
        print(f"✅ {file_path} ({size} bytes) - {description}")
        return True
    else:
        print(f"❌ {file_path} - {description} - MISSING!")
        return False

def check_deployment_readiness():
    """Check if the system is ready for deployment"""
    
    print("🏥 Hospital Management System - Deployment Readiness Check")
    print("=" * 70)
    
    all_checks_passed = True
    
    # Core application files
    print("\n📋 Core Application Files:")
    core_files = [
        ("run.py", "Application entry point"),
        ("config.py", "Configuration settings"),
        ("requirements.txt", "Python dependencies"),
        (".env", "Environment variables"),
        ("init_db.py", "Database initialization script"),
        ("README.md", "Documentation")
    ]
    
    for file_path, description in core_files:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # App structure
    print("\n🏗️ Application Structure:")
    app_structure = [
        ("app/__init__.py", "App factory"),
        ("app/models.py", "Database models"),
        ("app/auth/decorators.py", "Authentication decorators"),
        ("app/utils/helpers.py", "Helper functions")
    ]
    
    for file_path, description in app_structure:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # Routes
    print("\n🛣️ API Routes:")
    routes = [
        ("app/routes/main.py", "Main routes"),
        ("app/routes/auth.py", "Authentication routes"),
        ("app/routes/user.py", "User routes"),
        ("app/routes/hospital.py", "Hospital routes"),
        ("app/routes/doctor.py", "Doctor routes"),
        ("app/routes/appointment.py", "Appointment routes"),
        ("app/routes/blood_bank.py", "Blood bank routes"),
        ("app/routes/emergency.py", "Emergency routes"),
        ("app/routes/admin.py", "Admin routes"),
        ("app/routes/dashboard.py", "Dashboard routes"),
        ("app/routes/reporting.py", "Reporting routes"),
        ("app/routes/audit.py", "Audit routes"),
        ("app/routes/notifications.py", "Notification routes")
    ]
    
    for file_path, description in routes:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # Services
    print("\n🔧 Enhanced Services:")
    services = [
        ("app/services/email_service.py", "Email service"),
        ("app/services/websocket_service.py", "WebSocket service"),
        ("app/services/cache_service.py", "Cache service"),
        ("app/services/rate_limiter.py", "Rate limiting"),
        ("app/services/audit_service.py", "Audit service"),
        ("app/services/reporting_service.py", "Reporting service")
    ]
    
    for file_path, description in services:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # Frontend assets
    print("\n🎨 Frontend Assets:")
    frontend_assets = [
        ("static/css/main.css", "Main stylesheet"),
        ("static/js/main.js", "Main JavaScript"),
        ("static/uploads/", "Upload directory"),
        ("static/images/", "Images directory"),
        ("static/assets/", "Assets directory")
    ]
    
    for file_path, description in frontend_assets:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # Templates
    print("\n📄 Essential Templates:")
    essential_templates = [
        ("app/templates/base.html", "Base template"),
        ("app/templates/landing_page.html", "Landing page"),
        ("app/templates/user_login.html", "Login page"),
        ("app/templates/user_register.html", "Registration page"),
        ("app/templates/user_dashboard.html", "User dashboard"),
        ("app/templates/hospital_list_complete.html", "Hospital listing"),
        ("app/templates/faq.html", "FAQ page"),
        ("app/templates/errors/404.html", "404 error page"),
        ("app/templates/errors/500.html", "500 error page")
    ]
    
    for file_path, description in essential_templates:
        if not check_file_exists(file_path, description):
            all_checks_passed = False
    
    # Check for critical configuration
    print("\n⚙️ Configuration Check:")
    
    # Check .env file content
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
            
        required_env_vars = ['SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL']
        for var in required_env_vars:
            if var in env_content:
                print(f"✅ {var} configured in .env")
            else:
                print(f"❌ {var} missing from .env")
                all_checks_passed = False
    
    # Check requirements.txt content
    if os.path.exists('requirements.txt'):
        with open('requirements.txt', 'r') as f:
            requirements_content = f.read()
            
        required_packages = ['Flask', 'Flask-SQLAlchemy', 'Flask-JWT-Extended', 'python-dotenv']
        for package in required_packages:
            if package in requirements_content:
                print(f"✅ {package} in requirements.txt")
            else:
                print(f"❌ {package} missing from requirements.txt")
                all_checks_passed = False
    
    # Final verdict
    print("\n" + "=" * 70)
    if all_checks_passed:
        print("🎉 DEPLOYMENT READY! Your Hospital Management System is complete and ready to deploy!")
        print("\n🚀 Next Steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Initialize database: python init_db.py")
        print("3. Start application: python run.py")
        print("4. Access at: http://localhost:5000")
        print("\n🔑 Default Login Credentials:")
        print("   • Admin: username='admin', password='admin123'")
        print("   • User: username='john_doe', password='password123'")
        print("   • Hospital: username='city_general', password='hospital123'")
    else:
        print("❌ DEPLOYMENT NOT READY! Some files are missing.")
        print("Please check the missing items above before deploying.")
    
    return all_checks_passed

def check_python_imports():
    """Test critical imports"""
    print("\n🐍 Python Import Test:")
    
    critical_imports = [
        "os",
        "sys", 
        "datetime",
        "pathlib"
    ]
    
    for module in critical_imports:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            return False
    
    return True

if __name__ == '__main__':
    print("Starting deployment readiness verification...\n")
    
    # Check Python imports first
    if not check_python_imports():
        print("❌ Critical Python imports failed!")
        sys.exit(1)
    
    # Check deployment readiness
    is_ready = check_deployment_readiness()
    
    if is_ready:
        print("\n✅ System is DEPLOYMENT READY!")
        sys.exit(0)
    else:
        print("\n❌ System is NOT ready for deployment!")
        sys.exit(1)
