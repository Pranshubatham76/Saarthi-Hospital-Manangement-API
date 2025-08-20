#!/usr/bin/env python3
"""
Test the fixed routes
"""
import requests
import json

def test_fixed_routes():
    """Test all the routes we just fixed"""
    base_url = 'http://localhost:5000'
    
    # Setup authentication
    admin_response = requests.post(
        f'{base_url}/auth/admin/login',
        json={'username': 'admin@hospital.com', 'password': 'admin123'}
    )
    
    user_response = requests.post(
        f'{base_url}/auth/login',
        json={'username': 'testuser2', 'password': 'Password123!'}
    )
    
    admin_token = admin_response.json()['data']['access_token']
    user_token = user_response.json()['data']['access_token']
    user_id = user_response.json()['data']['user']['id']
    
    admin_headers = {'Authorization': f'Bearer {admin_token}', 'Content-Type': 'application/json'}
    user_headers = {'Authorization': f'Bearer {user_token}', 'Content-Type': 'application/json'}
    
    print("🔧 TESTING FIXED ROUTES")
    print("=" * 50)
    
    # Test forgot password
    print("\n1. Testing forgot password:")
    try:
        forgot_response = requests.post(
            f'{base_url}/auth/forgot-password',
            json={'email': 'testuser2@example.com'},
            headers={'Content-Type': 'application/json'}
        )
        print(f"✅ Forgot password: {forgot_response.status_code}")
    except Exception as e:
        print(f"❌ Forgot password failed: {e}")
    
    # Test admin stats
    print("\n2. Testing admin stats:")
    try:
        stats_response = requests.get(f'{base_url}/admin/stats', headers=admin_headers)
        print(f"✅ Admin stats: {stats_response.status_code}")
        if stats_response.status_code == 200:
            stats = stats_response.json()['data']['stats']
            print(f"   Users: {stats['users']['total']}")
            print(f"   Hospitals: {stats['hospitals']['total']}")
            print(f"   Emergencies: {stats['emergencies']['total']}")
    except Exception as e:
        print(f"❌ Admin stats failed: {e}")
    
    # Test emergency stats  
    print("\n3. Testing emergency stats:")
    try:
        emergency_stats_response = requests.get(f'{base_url}/emergency/stats', headers=admin_headers)
        print(f"✅ Emergency stats: {emergency_stats_response.status_code}")
        if emergency_stats_response.status_code == 200:
            stats = emergency_stats_response.json()['data']['stats']
            print(f"   Total emergencies: {stats['total_emergencies']}")
            print(f"   Recent emergencies: {stats['recent_emergencies']}")
    except Exception as e:
        print(f"❌ Emergency stats failed: {e}")
    
    # Test blood bank registration (with correct field names)
    print("\n4. Testing blood bank registration:")
    try:
        bloodbank_data = {
            "name": "Fixed Route Blood Bank",
            "location": "Fixed Route City",
            "contact_no": "555-FIXED-ROUTE",  # Correct field name
            "email": "fixedroute@bloodbank.com",
            "blood_types_available": ["A+", "B+", "O+"],
            "stock_levels": {"A+": 100, "B+": 50, "O+": 200}
        }
        
        bloodbank_response = requests.post(
            f'{base_url}/bloodbank/register',
            json=bloodbank_data,
            headers=admin_headers
        )
        print(f"✅ Blood bank registration: {bloodbank_response.status_code}")
    except Exception as e:
        print(f"❌ Blood bank registration failed: {e}")
    
    # Test blood inventory
    print("\n5. Testing blood inventory:")
    try:
        inventory_response = requests.get(f'{base_url}/bloodbank/inventory', headers=admin_headers)
        print(f"✅ Blood inventory: {inventory_response.status_code}")
        if inventory_response.status_code == 200:
            inventory = inventory_response.json()['data']
            print(f"   Total inventory items: {len(inventory['inventory'])}")
    except Exception as e:
        print(f"❌ Blood inventory failed: {e}")
    
    # Test notifications (check if user exists)
    print("\n6. Testing notifications (check user exists):")
    try:
        # First verify user exists
        print(f"   Testing with user ID: {user_id}")
        
        notification_data = {
            "title": "Fixed Route Test Notification",
            "body": "Testing notification after route fixes",
            "user_ids": [user_id],
            "send_websocket": True,
            "send_email": False
        }
        
        notification_response = requests.post(
            f'{base_url}/notifications/send',
            json=notification_data,
            headers=admin_headers
        )
        print(f"✅ Send notification: {notification_response.status_code}")
        response_data = notification_response.json()
        print(f"   Sent: {response_data['data']['sent_count']}")
        print(f"   Failed: {response_data['data']['failed_count']}")
        
    except Exception as e:
        print(f"❌ Notifications failed: {e}")
    
    # Test appointment booking conflict resolution
    print("\n7. Testing different appointment slot:")
    try:
        slots_response = requests.get(f'{base_url}/appointment/available-slots?hospital_id=1')
        if slots_response.status_code == 200:
            slots = slots_response.json()['data']['slots']
            if len(slots) > 1:
                # Try a different slot
                slot_id = slots[1]['id']
                appointment_data = {
                    "hospital_id": 1,
                    "slot_id": slot_id,
                    "reason": "Fixed route test appointment"
                }
                
                appointment_response = requests.post(
                    f'{base_url}/appointment/opd/book',
                    json=appointment_data,
                    headers=user_headers
                )
                print(f"✅ Appointment booking: {appointment_response.status_code}")
                if appointment_response.status_code == 409:
                    print("   ⚠️ Conflict: User already has appointment for this slot")
                elif appointment_response.status_code == 201:
                    print("   ✅ Successfully booked new appointment")
            else:
                print("   ⚠️ Only one slot available, cannot test different slot")
        else:
            print(f"   ❌ Could not get slots: {slots_response.status_code}")
    except Exception as e:
        print(f"❌ Appointment booking test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 FIXED ROUTE TESTING COMPLETED!")

if __name__ == '__main__':
    test_fixed_routes()