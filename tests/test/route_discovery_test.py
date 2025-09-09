#!/usr/bin/env python3
"""
Route Discovery and Testing Script
Discovers all Flask routes and tests them systematically
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_route_discovery():
    """Discover and test basic routes"""
    print("🔍 Testing Route Discovery")
    print("=" * 50)
    
    # Test basic endpoints first
    basic_endpoints = [
        "/",
        "/health", 
        "/api/info",
    ]
    
    for endpoint in basic_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            status = "✅ PASS" if response.status_code == 200 else "❌ FAIL"
            print(f"{status} GET {endpoint} -> {response.status_code}")
        except Exception as e:
            print(f"❌ FAIL GET {endpoint} -> ERROR: {e}")
    
    print("\n🔐 Testing Authentication Endpoints")
    print("=" * 50)
    
    # Test authentication endpoints (should return appropriate status codes)
    auth_endpoints = [
        ("/auth/register", "POST"),
        ("/auth/login", "POST"), 
        ("/auth/admin/login", "POST"),
        ("/auth/hospital/login", "POST"),
        ("/auth/profile", "GET"),
        ("/auth/logout", "POST"),
    ]
    
    for endpoint, method in auth_endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", json={}, timeout=10)
            
            # Auth endpoints should return 400/401/422 for missing data, not 500
            acceptable_codes = [200, 201, 400, 401, 422]
            status = "✅ PASS" if response.status_code in acceptable_codes else "❌ FAIL"
            print(f"{status} {method} {endpoint} -> {response.status_code}")
        except Exception as e:
            print(f"❌ FAIL {method} {endpoint} -> ERROR: {e}")
    
    print("\n🏥 Testing Public Hospital Endpoints")
    print("=" * 50)
    
    # Test public hospital endpoints
    hospital_endpoints = [
        "/hospital/all",
        "/doctor/all", 
        "/bloodbank/all",
    ]
    
    for endpoint in hospital_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            status = "✅ PASS" if response.status_code == 200 else "❌ FAIL"
            print(f"{status} GET {endpoint} -> {response.status_code}")
        except Exception as e:
            print(f"❌ FAIL GET {endpoint} -> ERROR: {e}")
    
    print("\n🔒 Testing Protected Endpoints (Expected 401)")
    print("=" * 50)
    
    # Test protected endpoints (should return 401 without auth)
    protected_endpoints = [
        "/user/all",
        "/admin/dashboard/stats",
        "/dashboard/",
        "/appointment/my-appointments",
    ]
    
    for endpoint in protected_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            status = "✅ PASS" if response.status_code == 401 else "❌ FAIL"
            print(f"{status} GET {endpoint} -> {response.status_code} (expected 401)")
        except Exception as e:
            print(f"❌ FAIL GET {endpoint} -> ERROR: {e}")

def test_error_handling():
    """Test error handling for non-existent routes"""
    print("\n🚫 Testing Error Handling")
    print("=" * 50)
    
    # Test non-existent routes
    invalid_endpoints = [
        "/nonexistent",
        "/api/nonexistent",
        "/hospital/999999",
        "/user/999999",
    ]
    
    for endpoint in invalid_endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            status = "✅ PASS" if response.status_code == 404 else "❌ FAIL"
            print(f"{status} GET {endpoint} -> {response.status_code} (expected 404)")
        except Exception as e:
            print(f"❌ FAIL GET {endpoint} -> ERROR: {e}")

def test_method_not_allowed():
    """Test method not allowed errors"""
    print("\n🚫 Testing Method Not Allowed")
    print("=" * 50)
    
    # Test wrong methods on existing endpoints
    method_tests = [
        ("/health", "POST"),
        ("/api/info", "POST"),
        ("/hospital/all", "POST"),
        ("/doctor/all", "POST"),
    ]
    
    for endpoint, method in method_tests:
        try:
            if method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", timeout=10)
            elif method == "PUT":
                response = requests.put(f"{BASE_URL}{endpoint}", timeout=10)
            elif method == "DELETE":
                response = requests.delete(f"{BASE_URL}{endpoint}", timeout=10)
            
            status = "✅ PASS" if response.status_code == 405 else "❌ FAIL"
            print(f"{status} {method} {endpoint} -> {response.status_code} (expected 405)")
        except Exception as e:
            print(f"❌ FAIL {method} {endpoint} -> ERROR: {e}")

def main():
    """Main test function"""
    print(f"🏥 Hospital Management System Route Testing")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 Testing against: {BASE_URL}")
    print("=" * 70)
    
    test_route_discovery()
    test_error_handling()
    test_method_not_allowed()
    
    print("\n" + "=" * 70)
    print("🎉 Route Discovery Testing Complete!")
    print(f"📅 Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()