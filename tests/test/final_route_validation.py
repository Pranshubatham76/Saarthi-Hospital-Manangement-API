#!/usr/bin/env python3
"""
Final Route Validation Script
Tests all critical routes with proper authentication
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

class APIValidator:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        
    def log_test(self, name, method, url, expected_status, actual_status, success, note=None):
        """Log test result"""
        result = {
            'name': name,
            'method': method,
            'url': url,
            'expected': expected_status,
            'actual': actual_status,
            'success': success,
            'note': note or ''
        }
        self.test_results.append(result)
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} {method} {url} -> {actual_status} {note or ''}")
        
    def test_endpoint(self, method, path, expected_status=200, auth_token=None, json_data=None, name=None):
        """Test a single endpoint"""
        url = f"{BASE_URL}{path}"
        headers = {"Content-Type": "application/json"}
        
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
            
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = self.session.post(url, headers=headers, json=json_data or {}, timeout=10)
            elif method == "PUT":
                response = self.session.put(url, headers=headers, json=json_data or {}, timeout=10)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            success = response.status_code == expected_status
            self.log_test(name or path, method, url, expected_status, response.status_code, success)
            
            return response
            
        except Exception as e:
            self.log_test(name or path, method, url, expected_status, "ERROR", False, str(e))
            return None
    
    def authenticate(self):
        """Get authentication tokens"""
        print("🔑 Setting up authentication...")
        
        # Register a test user
        user_data = {
            'username': f'test_user_{int(time.time())}',
            'fullname': 'Test User',
            'email': f'test_{int(time.time())}@example.com',
            'password': 'SecurePass123!',
            'phone_num': '+1234567890',
            'role': 'user'
        }
        
        # Register user
        self.test_endpoint("POST", "/auth/register", 201, json_data=user_data, name="auth:register")
        
        # Login user
        login_response = self.test_endpoint("POST", "/auth/login", 200, 
                                          json_data={'username': user_data['username'], 'password': user_data['password']},
                                          name="auth:user_login")
        
        if login_response and login_response.status_code == 200:
            data = login_response.json().get('data', {})
            self.tokens['user'] = data.get('access_token')
            
        # Login admin
        admin_response = self.test_endpoint("POST", "/auth/admin/login", 200,
                                          json_data={'username': 'admin@hospital.com', 'password': 'admin123'},
                                          name="auth:admin_login")
        
        if admin_response and admin_response.status_code == 200:
            data = admin_response.json().get('data', {})
            self.tokens['admin'] = data.get('access_token')
            
        # Login hospital
        hospital_response = self.test_endpoint("POST", "/auth/hospital/login", 200,
                                             json_data={'username': 'city_general', 'password': 'hospital123'},
                                             name="auth:hospital_login")
        
        if hospital_response and hospital_response.status_code == 200:
            data = hospital_response.json().get('data', {})
            self.tokens['hospital'] = data.get('access_token')
            
        print(f"Tokens obtained: User={bool(self.tokens.get('user'))}, Admin={bool(self.tokens.get('admin'))}, Hospital={bool(self.tokens.get('hospital'))}")
        
    def test_public_routes(self):
        """Test public routes"""
        print("\n🌐 Testing Public Routes")
        print("=" * 50)
        
        public_routes = [
            ("GET", "/", 200),
            ("GET", "/health", 200),
            ("GET", "/api/info", 200),
            ("GET", "/hospital/all", 200),
            ("GET", "/doctor/all", 200),
            ("GET", "/bloodbank/all", 200),
            ("POST", "/contact", 201),
        ]
        
        for method, path, expected in public_routes:
            json_data = {'name': 'Test', 'email': 'test@example.com', 'message': 'Test message'} if path == '/contact' else None
            self.test_endpoint(method, path, expected, json_data=json_data)
    
    def test_user_routes(self):
        """Test user-specific routes"""
        print("\n👤 Testing User Routes")
        print("=" * 50)
        
        if not self.tokens.get('user'):
            print("❌ No user token available, skipping user routes")
            return
            
        user_routes = [
            ("GET", "/auth/profile", 200),
            ("GET", "/appointment/my-appointments", 200),
            ("GET", "/appointment/available-slots", 200),
            ("GET", "/bloodbank/requests", 200),
            ("GET", "/notifications/my-notifications", 200),
            ("GET", "/notifications/unread-count", 200),
        ]
        
        for method, path, expected in user_routes:
            params = {'hospital_id': 1} if 'available-slots' in path else None
            if params:
                # For GET with params, we need to handle it differently
                url = f"{BASE_URL}{path}?hospital_id=1"
                headers = {"Authorization": f"Bearer {self.tokens['user']}"}
                try:
                    response = self.session.get(url, headers=headers, timeout=10)
                    success = response.status_code == expected
                    self.log_test(path, method, url, expected, response.status_code, success)
                except Exception as e:
                    self.log_test(path, method, url, expected, "ERROR", False, str(e))
            else:
                self.test_endpoint(method, path, expected, auth_token=self.tokens['user'])
    
    def test_admin_routes(self):
        """Test admin-specific routes"""
        print("\n👨‍💼 Testing Admin Routes")
        print("=" * 50)
        
        if not self.tokens.get('admin'):
            print("❌ No admin token available, skipping admin routes")
            return
            
        admin_routes = [
            ("GET", "/admin/dashboard/stats", 200),
            ("GET", "/admin/logs", 200),
            ("GET", "/user/all", 200),
            ("GET", "/user/stats", 200),
            ("GET", "/audit/logs", 200),
            ("GET", "/audit/security-summary", 200),
        ]
        
        for method, path, expected in admin_routes:
            self.test_endpoint(method, path, expected, auth_token=self.tokens['admin'])
    
    def test_error_conditions(self):
        """Test error conditions"""
        print("\n🚫 Testing Error Conditions")
        print("=" * 50)
        
        error_tests = [
            ("GET", "/nonexistent", 404),
            ("GET", "/hospital/999999", 404),
            ("GET", "/doctor/999999", 404),
            ("POST", "/health", 405),  # Method not allowed
            ("POST", "/api/info", 405),  # Method not allowed
            ("GET", "/user/all", 401),  # Unauthorized (no token)
            ("GET", "/admin/dashboard/stats", 401),  # Unauthorized (no token)
        ]
        
        for method, path, expected in error_tests:
            self.test_endpoint(method, path, expected)
    
    def run_validation(self):
        """Run complete validation"""
        print("🏥 Hospital Management System - Final Route Validation")
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        self.authenticate()
        self.test_public_routes()
        self.test_user_routes()
        self.test_admin_routes()
        self.test_error_conditions()
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 80)
        print("📊 FINAL VALIDATION SUMMARY")
        print("=" * 80)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['method']} {result['name']} -> {result['actual']} (expected {result['expected']}) {result['note']}")
        
        print(f"\n📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return failed_tests == 0

def main():
    validator = APIValidator()
    success = validator.run_validation()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())