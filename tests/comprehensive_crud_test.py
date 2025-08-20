#!/usr/bin/env python3
"""
Comprehensive CRUD operations testing
"""
import requests
import json
from datetime import datetime, timedelta

class CRUDTester:
    def __init__(self):
        self.base_url = 'http://localhost:5000'
        self.admin_token = None
        self.user_token = None
        self.user_id = None
        
    def setup_authentication(self):
        """Setup authentication tokens"""
        print("🔑 Setting up authentication...")
        
        # Admin login
        admin_response = requests.post(
            f'{self.base_url}/auth/admin/login',
            json={'username': 'admin@hospital.com', 'password': 'admin123'}
        )
        
        if admin_response.status_code == 200:
            self.admin_token = admin_response.json()['data']['access_token']
            print("✅ Admin authentication successful")
        else:
            print(f"❌ Admin authentication failed: {admin_response.status_code}")
            return False
            
        # User login
        user_response = requests.post(
            f'{self.base_url}/auth/login',
            json={'username': 'testuser2', 'password': 'Password123!'}
        )
        
        if user_response.status_code == 200:
            user_data = user_response.json()['data']
            self.user_token = user_data['access_token']
            self.user_id = user_data['user']['id']
            print("✅ User authentication successful")
        else:
            print(f"❌ User authentication failed: {user_response.status_code}")
            return False
            
        return True
    
    def admin_headers(self):
        return {'Authorization': f'Bearer {self.admin_token}', 'Content-Type': 'application/json'}
    
    def user_headers(self):
        return {'Authorization': f'Bearer {self.user_token}', 'Content-Type': 'application/json'}
    
    def test_hospital_crud(self):
        """Test Hospital CRUD operations"""
        print("\n🏥 Testing Hospital CRUD Operations")
        
        # CREATE - Register new hospital
        hospital_data = {
            "name": "Test CRUD Hospital",
            "location": "CRUD Test City",
            "contactNumber": "555-CRUD-001",
            "email": "crud@test-hospital.com",
            "hospital_type": "Multi-specialty",
            "bedAvailability": 100,
            "oxygenUnits": 20,
            "opd_status": True
        }
        
        create_response = requests.post(
            f'{self.base_url}/hospital/register',
            json=hospital_data,
            headers=self.admin_headers()
        )
        
        if create_response.status_code == 201:
            hospital = create_response.json()['data']['hospital']
            hospital_id = hospital['id']
            print(f"✅ CREATE Hospital: ID {hospital_id}")
            
            # READ - Get hospital details
            read_response = requests.get(
                f'{self.base_url}/hospital/{hospital_id}',
                headers=self.admin_headers()
            )
            
            if read_response.status_code == 200:
                print("✅ READ Hospital: Details retrieved")
            else:
                print(f"❌ READ Hospital failed: {read_response.status_code}")
            
            # UPDATE - Modify hospital
            update_data = {
                "name": "Updated CRUD Hospital",
                "bedAvailability": 150
            }
            
            update_response = requests.put(
                f'{self.base_url}/hospital/update/{hospital_id}',
                json=update_data,
                headers=self.admin_headers()
            )
            
            if update_response.status_code == 200:
                print("✅ UPDATE Hospital: Successfully modified")
            else:
                print(f"❌ UPDATE Hospital failed: {update_response.status_code}")
            
            # DELETE - Remove hospital
            delete_response = requests.delete(
                f'{self.base_url}/hospital/delete/{hospital_id}',
                headers=self.admin_headers()
            )
            
            if delete_response.status_code == 200:
                print("✅ DELETE Hospital: Successfully removed")
            else:
                print(f"❌ DELETE Hospital failed: {delete_response.status_code}")
                
        else:
            print(f"❌ CREATE Hospital failed: {create_response.status_code} - {create_response.text}")
    
    def test_user_crud(self):
        """Test User CRUD operations"""
        print("\n👤 Testing User CRUD Operations")
        
        # CREATE - Register new user
        user_data = {
            "username": "crudtestuser",
            "email": "crudtest@example.com",
            "password": "CrudTest123!",
            "firstName": "CRUD",
            "lastName": "Tester",
            "phoneNumber": "555-CRUD-USER"
        }
        
        create_response = requests.post(
            f'{self.base_url}/auth/register',
            json=user_data
        )
        
        if create_response.status_code == 201:
            user = create_response.json()['data']['user']
            user_id = user['id']
            print(f"✅ CREATE User: ID {user_id}")
            
            # READ - Get user profile (as admin)
            read_response = requests.get(
                f'{self.base_url}/admin/users/{user_id}',
                headers=self.admin_headers()
            )
            
            if read_response.status_code == 200:
                print("✅ READ User: Profile retrieved")
            else:
                print(f"❌ READ User failed: {read_response.status_code}")
            
            # UPDATE - User can update their own profile
            # First, login as the new user
            login_response = requests.post(
                f'{self.base_url}/auth/login',
                json={'username': 'crudtestuser', 'password': 'CrudTest123!'}
            )
            
            if login_response.status_code == 200:
                new_user_token = login_response.json()['data']['access_token']
                new_user_headers = {'Authorization': f'Bearer {new_user_token}', 'Content-Type': 'application/json'}
                
                update_data = {
                    "firstName": "Updated CRUD",
                    "phoneNumber": "555-UPDATED"
                }
                
                update_response = requests.put(
                    f'{self.base_url}/auth/profile',
                    json=update_data,
                    headers=new_user_headers
                )
                
                if update_response.status_code == 200:
                    print("✅ UPDATE User: Profile updated")
                else:
                    print(f"❌ UPDATE User failed: {update_response.status_code}")
            
            # DELETE - Admin can delete user
            delete_response = requests.delete(
                f'{self.base_url}/admin/users/{user_id}',
                headers=self.admin_headers()
            )
            
            if delete_response.status_code == 200:
                print("✅ DELETE User: Successfully removed")
            else:
                print(f"❌ DELETE User failed: {delete_response.status_code}")
                
        else:
            print(f"❌ CREATE User failed: {create_response.status_code} - {create_response.text}")
    
    def test_appointment_crud(self):
        """Test Appointment CRUD operations"""
        print("\n📅 Testing Appointment CRUD Operations")
        
        # First, get available slots
        slots_response = requests.get(
            f'{self.base_url}/appointment/available-slots?hospital_id=1',
        )
        
        if slots_response.status_code == 200 and slots_response.json()['data']['slots']:
            slot = slots_response.json()['data']['slots'][0]
            slot_id = slot['id']
            
            # CREATE - Book appointment
            appointment_data = {
                "hospital_id": 1,
                "slot_id": slot_id,
                "reason": "CRUD test appointment"
            }
            
            create_response = requests.post(
                f'{self.base_url}/appointment/opd/book',
                json=appointment_data,
                headers=self.user_headers()
            )
            
            if create_response.status_code == 201:
                appointment = create_response.json()['data']['appointment']
                appointment_id = appointment['id']
                print(f"✅ CREATE Appointment: ID {appointment_id}")
                
                # READ - Get appointment details
                read_response = requests.get(
                    f'{self.base_url}/appointment/{appointment_id}',
                    headers=self.user_headers()
                )
                
                if read_response.status_code == 200:
                    print("✅ READ Appointment: Details retrieved")
                else:
                    print(f"❌ READ Appointment failed: {read_response.status_code}")
                
                # UPDATE - Modify appointment (reschedule if available)
                update_data = {
                    "reason": "Updated CRUD test appointment"
                }
                
                update_response = requests.put(
                    f'{self.base_url}/appointment/update/{appointment_id}',
                    json=update_data,
                    headers=self.user_headers()
                )
                
                if update_response.status_code == 200:
                    print("✅ UPDATE Appointment: Successfully modified")
                elif update_response.status_code == 404:
                    print("⚠️ UPDATE Appointment: Endpoint not found (may not be implemented)")
                else:
                    print(f"❌ UPDATE Appointment failed: {update_response.status_code}")
                
                # DELETE - Cancel appointment
                delete_response = requests.delete(
                    f'{self.base_url}/appointment/cancel/{appointment_id}',
                    headers=self.user_headers()
                )
                
                if delete_response.status_code == 200:
                    print("✅ DELETE Appointment: Successfully cancelled")
                else:
                    print(f"❌ DELETE Appointment failed: {delete_response.status_code}")
                    
            else:
                print(f"❌ CREATE Appointment failed: {create_response.status_code} - {create_response.text}")
        else:
            print("⚠️ No available slots found for appointment testing")
    
    def test_notifications_crud(self):
        """Test Notifications CRUD operations"""
        print("\n📢 Testing Notifications CRUD Operations")
        
        # CREATE - Send notification
        notification_data = {
            "title": "CRUD Test Notification",
            "body": "This is a comprehensive CRUD test notification",
            "user_ids": [self.user_id],
            "send_websocket": True,
            "send_email": False,
            "metadata": {"test": True, "type": "crud_test"}
        }
        
        create_response = requests.post(
            f'{self.base_url}/notifications/send',
            json=notification_data,
            headers=self.admin_headers()
        )
        
        if create_response.status_code == 201:
            print("✅ CREATE Notification: Successfully sent")
            
            # READ - Get user's notifications
            read_response = requests.get(
                f'{self.base_url}/notifications/my-notifications',
                headers=self.user_headers()
            )
            
            if read_response.status_code == 200:
                notifications = read_response.json()['data']['notifications']
                print(f"✅ READ Notifications: {len(notifications)} found")
                
                if notifications:
                    notification_id = notifications[0]['id']
                    
                    # UPDATE - Mark notification as read
                    update_response = requests.put(
                        f'{self.base_url}/notifications/{notification_id}/read',
                        headers=self.user_headers()
                    )
                    
                    if update_response.status_code == 200:
                        print("✅ UPDATE Notification: Marked as read")
                    else:
                        print(f"❌ UPDATE Notification failed: {update_response.status_code}")
                    
                    # DELETE - Delete notification
                    delete_response = requests.delete(
                        f'{self.base_url}/notifications/{notification_id}',
                        headers=self.user_headers()
                    )
                    
                    if delete_response.status_code == 200:
                        print("✅ DELETE Notification: Successfully removed")
                    else:
                        print(f"❌ DELETE Notification failed: {delete_response.status_code}")
            else:
                print(f"❌ READ Notifications failed: {read_response.status_code}")
                
        else:
            print(f"❌ CREATE Notification failed: {create_response.status_code} - {create_response.text}")
    
    def test_emergency_crud(self):
        """Test Emergency CRUD operations"""
        print("\n🚨 Testing Emergency CRUD Operations")
        
        # CREATE - Log emergency
        emergency_data = {
            "emergency_type": "Medical",
            "location": "CRUD Test Location",
            "contact_number": "555-EMERGENCY",
            "details": "CRUD test emergency case",
            "user_id": self.user_id
        }
        
        create_response = requests.post(
            f'{self.base_url}/emergency/call',
            json=emergency_data
        )
        
        if create_response.status_code == 201:
            emergency = create_response.json()['data']['emergency']
            emergency_id = emergency['id']
            print(f"✅ CREATE Emergency: ID {emergency_id}")
            
            # READ - Get emergency details (admin access)
            read_response = requests.get(
                f'{self.base_url}/emergency/{emergency_id}',
                headers=self.admin_headers()
            )
            
            if read_response.status_code == 200:
                print("✅ READ Emergency: Details retrieved")
            else:
                print(f"❌ READ Emergency failed: {read_response.status_code}")
            
            # UPDATE - Update emergency status
            update_data = {
                "forward_status": "processed",
                "assigned_hospital_id": 1
            }
            
            update_response = requests.put(
                f'{self.base_url}/emergency/update/{emergency_id}',
                json=update_data,
                headers=self.admin_headers()
            )
            
            if update_response.status_code == 200:
                print("✅ UPDATE Emergency: Status updated")
            else:
                print(f"❌ UPDATE Emergency failed: {update_response.status_code}")
            
            # READ ALL - Get all emergencies (admin)
            read_all_response = requests.get(
                f'{self.base_url}/emergency/all',
                headers=self.admin_headers()
            )
            
            if read_all_response.status_code == 200:
                emergencies = read_all_response.json()['data']['emergencies']
                print(f"✅ READ ALL Emergencies: {len(emergencies)} found")
            else:
                print(f"❌ READ ALL Emergencies failed: {read_all_response.status_code}")
                
        else:
            print(f"❌ CREATE Emergency failed: {create_response.status_code} - {create_response.text}")
    
    def run_all_tests(self):
        """Run all CRUD tests"""
        print("🧪 COMPREHENSIVE CRUD OPERATIONS TESTING")
        print("=========================================")
        
        if not self.setup_authentication():
            print("❌ Authentication setup failed. Aborting tests.")
            return
        
        self.test_hospital_crud()
        self.test_user_crud()
        self.test_appointment_crud()
        self.test_notifications_crud()
        self.test_emergency_crud()
        
        print("\n🏁 CRUD TESTING COMPLETED!")

if __name__ == '__main__':
    tester = CRUDTester()
    tester.run_all_tests()