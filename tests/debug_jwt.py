#!/usr/bin/env python3
"""
Debug JWT token validation and authentication
"""
import requests
import json
import jwt
from datetime import datetime

def test_token_generation_and_validation():
    """Test JWT token generation and validation"""
    print("=== JWT TOKEN DEBUGGING ===")
    
    # 1. Test Admin Login
    print("\n1. Testing Admin Login:")
    try:
        admin_response = requests.post(
            'http://localhost:5000/auth/admin/login',
            json={'username': 'admin@hospital.com', 'password': 'admin123'},
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Admin login status: {admin_response.status_code}")
        if admin_response.status_code == 200:
            admin_data = admin_response.json()
            admin_token = admin_data['data']['access_token']
            print(f"✅ Admin token received (length: {len(admin_token)})")
            print(f"Token preview: {admin_token[:50]}...")
            
            # Decode token to inspect claims
            try:
                # Note: This will fail because we don't have the secret, but we can see the header and payload
                decoded_header = jwt.get_unverified_header(admin_token)
                decoded_payload = jwt.decode(admin_token, options={"verify_signature": False})
                print(f"Token header: {decoded_header}")
                print(f"Token payload: {decoded_payload}")
            except Exception as e:
                print(f"Token inspection failed: {e}")
                
        else:
            print(f"❌ Admin login failed: {admin_response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Admin login exception: {e}")
        return None
    
    # 2. Test User Login
    print("\n2. Testing User Login:")
    try:
        user_response = requests.post(
            'http://localhost:5000/auth/login',
            json={'username': 'testuser2', 'password': 'Password123!'},
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"User login status: {user_response.status_code}")
        if user_response.status_code == 200:
            user_data = user_response.json()
            user_token = user_data['data']['access_token']
            print(f"✅ User token received (length: {len(user_token)})")
            
            # Decode token
            try:
                decoded_payload = jwt.decode(user_token, options={"verify_signature": False})
                print(f"User token payload: {decoded_payload}")
            except Exception as e:
                print(f"User token inspection failed: {e}")
                
        else:
            print(f"❌ User login failed: {user_response.text}")
            
    except Exception as e:
        print(f"❌ User login exception: {e}")
    
    # 3. Test Token Usage
    print("\n3. Testing Token Usage:")
    if 'admin_token' in locals():
        test_endpoints_with_token(admin_token, "admin")
    
    if 'user_token' in locals():
        test_endpoints_with_token(user_token, "user")

def test_endpoints_with_token(token, user_type):
    """Test various endpoints with the given token"""
    print(f"\n--- Testing endpoints with {user_type} token ---")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test different endpoints based on user type
    if user_type == "admin":
        endpoints_to_test = [
            ('GET', 'http://localhost:5000/notifications/my-notifications'),
            ('GET', 'http://localhost:5000/hospital/all'),
            ('GET', 'http://localhost:5000/emergency/all'),
            ('GET', 'http://localhost:5000/admin/hospitals'),
        ]
    else:
        endpoints_to_test = [
            ('GET', 'http://localhost:5000/notifications/my-notifications'),
            ('GET', 'http://localhost:5000/hospital/all'),
            ('GET', 'http://localhost:5000/appointment/my-appointments'),
        ]
    
    for method, url in endpoints_to_test:
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json={})
                
            print(f"  {method} {url.split('/')[-2:]}: {response.status_code}")
            
            if response.status_code == 401:
                print(f"    ❌ Unauthorized: {response.text[:100]}")
            elif response.status_code == 403:
                print(f"    ❌ Forbidden: {response.text[:100]}")
            elif 200 <= response.status_code < 300:
                print(f"    ✅ Success")
            else:
                print(f"    ⚠️ Other status: {response.text[:100]}")
                
        except Exception as e:
            print(f"  ❌ Exception for {url}: {e}")

def test_token_persistence():
    """Test if tokens work consistently across multiple requests"""
    print("\n4. Testing Token Persistence:")
    
    # Login and get token
    admin_response = requests.post(
        'http://localhost:5000/auth/admin/login',
        json={'username': 'admin@hospital.com', 'password': 'admin123'},
        headers={'Content-Type': 'application/json'}
    )
    
    if admin_response.status_code == 200:
        token = admin_response.json()['data']['access_token']
        
        # Make multiple requests with the same token
        for i in range(3):
            try:
                response = requests.get(
                    'http://localhost:5000/notifications/my-notifications',
                    headers={'Authorization': f'Bearer {token}'}
                )
                print(f"  Request {i+1}: Status {response.status_code}")
                
                if response.status_code != 200:
                    print(f"    Error: {response.text[:100]}")
                    
            except Exception as e:
                print(f"  Request {i+1} failed: {e}")

if __name__ == '__main__':
    test_token_generation_and_validation()
    test_token_persistence()
    
    print("\n=== JWT DEBUGGING COMPLETED ===")