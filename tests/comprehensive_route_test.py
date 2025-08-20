#!/usr/bin/env python3
"""
Comprehensive route testing to identify and fix issues
"""
import requests
import json
import traceback
from datetime import datetime

class RouteDebugger:
    def __init__(self):
        self.base_url = 'http://localhost:5000'
        self.admin_token = None
        self.user_token = None
        self.user_id = None
        self.failed_routes = []
        self.success_count = 0
        self.total_count = 0
        
    def authenticate(self):
        """Setup authentication"""
        print("🔑 Setting up authentication...")
        
        # Admin login
        try:
            admin_response = requests.post(
                f'{self.base_url}/auth/admin/login',
                json={'username': 'admin@hospital.com', 'password': 'admin123'},
                headers={'Content-Type': 'application/json'}
            )
            
            if admin_response.status_code == 200:
                self.admin_token = admin_response.json()['data']['access_token']
                print("✅ Admin authentication successful")
            else:
                print(f"❌ Admin auth failed: {admin_response.status_code}")
                print(f"Response: {admin_response.text}")
                return False
        except Exception as e:
            print(f"❌ Admin auth exception: {e}")
            return False
            
        # User login
        try:
            user_response = requests.post(
                f'{self.base_url}/auth/login',
                json={'username': 'testuser2', 'password': 'Password123!'},
                headers={'Content-Type': 'application/json'}
            )
            
            if user_response.status_code == 200:
                user_data = user_response.json()['data']
                self.user_token = user_data['access_token']
                self.user_id = user_data['user']['id']
                print("✅ User authentication successful")
                return True
            else:
                print(f"❌ User auth failed: {user_response.status_code}")
                print(f"Response: {user_response.text}")
                return False
        except Exception as e:
            print(f"❌ User auth exception: {e}")
            return False
    
    def admin_headers(self):
        return {'Authorization': f'Bearer {self.admin_token}', 'Content-Type': 'application/json'}
    
    def user_headers(self):
        return {'Authorization': f'Bearer {self.user_token}', 'Content-Type': 'application/json'}
    
    def test_route(self, method, endpoint, data=None, headers=None, expected_status=None, description=""):
        """Test a single route"""
        self.total_count += 1
        
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                print(f"❌ {method} {endpoint}: Unsupported method")
                return False
                
            # Check if response is successful
            is_success = (
                (expected_status and response.status_code == expected_status) or
                (not expected_status and 200 <= response.status_code < 300)
            )
            
            if is_success:
                print(f"✅ {method} {endpoint}: {response.status_code} {description}")
                self.success_count += 1
                return True
            else:
                print(f"❌ {method} {endpoint}: {response.status_code} {description}")
                print(f"   Response: {response.text[:200]}")
                self.failed_routes.append(f"{method} {endpoint}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ {method} {endpoint}: Request failed - {e}")
            self.failed_routes.append(f"{method} {endpoint}")
            return False
        except Exception as e:
            print(f"❌ {method} {endpoint}: Exception - {e}")
            print(f"   Traceback: {traceback.format_exc()}")
            self.failed_routes.append(f"{method} {endpoint}")
            return False
    
    def test_authentication_routes(self):
        """Test authentication related routes"""
        print("\n🔐 TESTING AUTHENTICATION ROUTES")
        print("=" * 50)
        
        # Test user registration with various field combinations
        test_users = [
            {
                "data": {
                    "username": "routetest1",
                    "fullname": "Route Test User 1", 
                    "email": "routetest1@test.com",
                    "password": "RouteTest123!",
                    "phone": "555-ROUTE-001"
                },
                "desc": "(with phone)"
            },
            {
                "data": {
                    "username": "routetest2",
                    "fullname": "Route Test User 2",
                    "email": "routetest2@test.com", 
                    "password": "RouteTest123!"
                },
                "desc": "(minimal fields)"
            }
        ]
        
        for i, user_test in enumerate(test_users):
            self.test_route(
                'POST', '/auth/register',
                data=user_test["data"],
                headers={'Content-Type': 'application/json'},
                expected_status=201,
                description=f"User registration {user_test['desc']}"
            )
        
        # Test profile operations
        self.test_route('GET', '/auth/profile', headers=self.user_headers(), description="Get user profile")
        
        # Test password reset request
        self.test_route(
            'POST', '/auth/forgot-password',
            data={'email': 'testuser2@example.com'},
            headers={'Content-Type': 'application/json'},
            description="Password reset request"
        )
    
    def test_hospital_routes(self):
        """Test hospital management routes"""
        print("\n🏥 TESTING HOSPITAL ROUTES")
        print("=" * 50)
        
        # Test hospital registration with various configurations
        test_hospitals = [
            {
                "data": {
                    "username": "testhospital_route1",
                    "name": "Route Test Hospital 1",
                    "type": "General",
                    "email": "hospital1@routetest.com", 
                    "password": "Hospital123!",
                    "location": "Route Test City 1",
                    "contact": "555-HOSP-001"
                },
                "desc": "(complete data)"
            },
            {
                "data": {
                    "username": "testhospital_route2", 
                    "name": "Route Test Hospital 2",
                    "type": "Specialty",
                    "email": "hospital2@routetest.com",
                    "password": "Hospital123!",
                    "location": "Route Test City 2"
                },
                "desc": "(without contact)"
            }
        ]
        
        created_hospital_id = None
        
        for hospital_test in test_hospitals:
            result = self.test_route(
                'POST', '/hospital/register',
                data=hospital_test["data"], 
                headers=self.admin_headers(),
                expected_status=201,
                description=f"Hospital registration {hospital_test['desc']}"
            )
            
            # Store the first successful hospital ID for further testing
            if result and not created_hospital_id:
                try:
                    response = requests.post(
                        f'{self.base_url}/hospital/register',
                        json=hospital_test["data"],
                        headers=self.admin_headers()
                    )
                    if response.status_code == 201:
                        created_hospital_id = response.json()['data']['hospital']['id']
                except:
                    pass
        
        # Test other hospital routes
        self.test_route('GET', '/hospital/all', headers=self.admin_headers(), description="Get all hospitals")
        
        if created_hospital_id:
            self.test_route(
                'GET', f'/hospital/{created_hospital_id}',
                headers=self.admin_headers(),
                description=f"Get hospital details (ID: {created_hospital_id})"
            )
            
            self.test_route(
                'PUT', f'/hospital/update/{created_hospital_id}',
                data={"name": "Updated Route Test Hospital", "bedAvailability": 200},
                headers=self.admin_headers(),
                description=f"Update hospital (ID: {created_hospital_id})"
            )
    
    def test_appointment_routes(self):
        """Test appointment system routes"""
        print("\n📅 TESTING APPOINTMENT ROUTES")
        print("=" * 50)
        
        # Test slot availability
        self.test_route(
            'GET', '/appointment/available-slots?hospital_id=1',
            description="Get available appointment slots"
        )
        
        # Test user's appointments
        self.test_route(
            'GET', '/appointment/my-appointments',
            headers=self.user_headers(),
            description="Get user's appointments"
        )
        
        # Test appointment booking (try to book if slots are available)
        try:
            slots_response = requests.get(f'{self.base_url}/appointment/available-slots?hospital_id=1')
            if slots_response.status_code == 200:
                slots_data = slots_response.json()
                if slots_data['data']['slots']:
                    slot_id = slots_data['data']['slots'][0]['id']
                    
                    self.test_route(
                        'POST', '/appointment/opd/book',
                        data={
                            "hospital_id": 1,
                            "slot_id": slot_id,
                            "reason": "Route testing appointment"
                        },
                        headers=self.user_headers(),
                        expected_status=201,
                        description=f"Book appointment (slot: {slot_id})"
                    )
        except:
            print("   ⚠️ Could not test appointment booking due to slot availability issues")
    
    def test_emergency_routes(self):
        """Test emergency system routes"""
        print("\n🚨 TESTING EMERGENCY ROUTES")
        print("=" * 50)
        
        # Test emergency call creation
        emergency_data = {
            "emergency_type": "Medical",
            "location": "Route Test Emergency Location",
            "contact_number": "555-EMERGENCY",
            "details": "Route testing emergency call",
            "user_id": self.user_id
        }
        
        self.test_route(
            'POST', '/emergency/call',
            data=emergency_data,
            headers={'Content-Type': 'application/json'},
            expected_status=201,
            description="Create emergency call"
        )
        
        # Test getting all emergencies (admin)
        self.test_route(
            'GET', '/emergency/all',
            headers=self.admin_headers(),
            description="Get all emergencies (admin)"
        )
        
        # Test emergency statistics
        self.test_route(
            'GET', '/emergency/stats',
            headers=self.admin_headers(), 
            description="Get emergency statistics"
        )
    
    def test_notification_routes(self):
        """Test notification system routes"""
        print("\n📢 TESTING NOTIFICATION ROUTES")
        print("=" * 50)
        
        # Test sending notifications
        notification_data = {
            "title": "Route Test Notification",
            "body": "This is a comprehensive route test notification",
            "user_ids": [self.user_id],
            "send_websocket": True,
            "send_email": False,
            "metadata": {"test_type": "route_testing"}
        }
        
        self.test_route(
            'POST', '/notifications/send',
            data=notification_data,
            headers=self.admin_headers(),
            expected_status=201,
            description="Send notification to user"
        )
        
        # Test getting user's notifications
        self.test_route(
            'GET', '/notifications/my-notifications',
            headers=self.user_headers(),
            description="Get user's notifications"
        )
        
        # Test getting unread notifications only
        self.test_route(
            'GET', '/notifications/my-notifications?unread_only=true',
            headers=self.user_headers(),
            description="Get unread notifications only"
        )
    
    def test_bloodbank_routes(self):
        """Test blood bank routes"""
        print("\n🩸 TESTING BLOOD BANK ROUTES")
        print("=" * 50)
        
        # Test blood bank registration
        bloodbank_data = {
            "name": "Route Test Blood Bank",
            "location": "Route Test City",
            "contact": "555-BLOOD-BANK", 
            "email": "bloodbank@routetest.com",
            "available_blood_types": ["A+", "B+", "O+", "AB+"],
            "capacity": 1000
        }
        
        self.test_route(
            'POST', '/bloodbank/register',
            data=bloodbank_data,
            headers=self.admin_headers(),
            expected_status=201,
            description="Register blood bank"
        )
        
        # Test getting all blood banks
        self.test_route(
            'GET', '/bloodbank/all',
            headers=self.admin_headers(),
            description="Get all blood banks"
        )
        
        # Test blood inventory
        self.test_route(
            'GET', '/bloodbank/inventory',
            headers=self.admin_headers(),
            description="Get blood inventory"
        )
    
    def test_misc_routes(self):
        """Test miscellaneous routes"""
        print("\n🔧 TESTING MISCELLANEOUS ROUTES")
        print("=" * 50)
        
        # Test API info
        self.test_route('GET', '/api/info', description="API information")
        
        # Test health check
        self.test_route('GET', '/health', description="Health check")
        
        # Test system stats (admin)
        self.test_route(
            'GET', '/admin/stats',
            headers=self.admin_headers(),
            description="System statistics (admin)"
        )
    
    def run_comprehensive_test(self):
        """Run all route tests"""
        print("🧪 COMPREHENSIVE ROUTE TESTING")
        print("=" * 70)
        
        if not self.authenticate():
            print("❌ Authentication failed. Cannot proceed with route testing.")
            return
        
        # Run all test suites
        self.test_authentication_routes()
        self.test_hospital_routes()
        self.test_appointment_routes()
        self.test_emergency_routes()
        self.test_notification_routes()
        self.test_bloodbank_routes()
        self.test_misc_routes()
        
        # Print final summary
        print("\n" + "=" * 70)
        print("🏁 ROUTE TESTING SUMMARY")
        print("=" * 70)
        print(f"✅ Successful routes: {self.success_count}/{self.total_count}")
        print(f"❌ Failed routes: {len(self.failed_routes)}/{self.total_count}")
        
        if self.failed_routes:
            print("\n❌ FAILED ROUTES:")
            for route in self.failed_routes:
                print(f"   - {route}")
        else:
            print("\n🎉 ALL ROUTES WORKING SUCCESSFULLY!")
        
        success_rate = (self.success_count / self.total_count * 100) if self.total_count > 0 else 0
        print(f"\n📊 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🟢 EXCELLENT: System is highly functional")
        elif success_rate >= 75:
            print("🟡 GOOD: Most features working, minor issues")
        elif success_rate >= 50:
            print("🟠 FAIR: Significant issues need addressing")
        else:
            print("🔴 POOR: Major system issues detected")

if __name__ == '__main__':
    debugger = RouteDebugger()
    debugger.run_comprehensive_test()