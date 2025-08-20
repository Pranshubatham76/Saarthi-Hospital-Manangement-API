#!/usr/bin/env python3
"""
Test the appointment endpoint manually
"""
import requests
from flask import Flask
from app import create_app

def test_appointment_endpoint():
    """Test appointment endpoint directly"""
    
    print("=== Testing Appointment Endpoint ===")
    
    # Test direct endpoint call
    try:
        response = requests.get(
            'http://localhost:5000/appointment/available-slots?hospital_id=1',
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Found {len(data['data']['slots'])} slots")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"Other error: {e}")

if __name__ == '__main__':
    test_appointment_endpoint()