#!/usr/bin/env python3
"""
Debug Appointment Access Issue
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"

def debug_appointment_access():
    """Debug the appointment access control issue"""
    print("🔍 Debugging Appointment Access Control")
    print("=" * 50)
    
    # Step 1: Register and login a user
    user_data = {
        'username': f'debug_user_{int(time.time())}',
        'fullname': 'Debug User',
        'email': f'debug_{int(time.time())}@example.com',
        'password': 'SecurePass123!',
        'phone_num': '+1234567890',
        'role': 'user'
    }
    
    # Register user
    register_response = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=10)
    print(f"Register: {register_response.status_code}")
    
    if register_response.status_code != 201:
        print(f"Registration failed: {register_response.text}")
        return
    
    # Login user
    login_response = requests.post(f"{BASE_URL}/auth/login", json={
        'username': user_data['username'],
        'password': user_data['password']
    }, timeout=10)
    print(f"Login: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
    
    # Get token and user info
    login_data = login_response.json().get('data', {})
    token = login_data.get('access_token')
    user = login_data.get('user', {})
    user_id = user.get('id')
    
    print(f"User ID: {user_id}")
    print(f"Token obtained: {bool(token)}")
    
    if not token:
        print("No token received")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Book an appointment
    print("\n📅 Booking an appointment...")
    
    # Get available slots first
    slots_response = requests.get(f"{BASE_URL}/appointment/available-slots", 
                                params={'hospital_id': 1}, timeout=10)
    print(f"Available slots: {slots_response.status_code}")
    
    if slots_response.status_code != 200:
        print("Could not get available slots")
        return
    
    slots_data = slots_response.json().get('data', {})
    slots = slots_data.get('slots', [])
    
    if not slots:
        print("No available slots")
        return
    
    slot = slots[0]
    slot_id = slot.get('id')
    print(f"Using slot ID: {slot_id}")
    
    # Book appointment
    booking_response = requests.post(f"{BASE_URL}/appointment/opd/book", 
                                   headers=headers,
                                   json={
                                       'hospital_id': 1,
                                       'slot_id': slot_id,
                                       'reason': 'Debug test appointment'
                                   }, timeout=10)
    
    print(f"Book appointment: {booking_response.status_code}")
    
    if booking_response.status_code != 201:
        print(f"Booking failed: {booking_response.text}")
        return
    
    # Step 3: Get appointment details from my-appointments
    print("\n📋 Getting my appointments...")
    my_appointments_response = requests.get(f"{BASE_URL}/appointment/my-appointments", 
                                          headers=headers, timeout=10)
    print(f"My appointments: {my_appointments_response.status_code}")
    
    if my_appointments_response.status_code != 200:
        print(f"Could not get my appointments: {my_appointments_response.text}")
        return
    
    appointments_data = my_appointments_response.json().get('data', {})
    appointments = appointments_data.get('appointments', [])
    
    if not appointments:
        print("No appointments found in my-appointments")
        return
    
    appointment = appointments[0]
    appointment_id = appointment.get('id')
    patient_id = appointment.get('patient_id')
    
    print(f"Found appointment ID: {appointment_id}")
    print(f"Appointment patient_id: {patient_id}")
    print(f"Current user_id: {user_id}")
    print(f"IDs match: {patient_id == user_id}")
    
    # Step 4: Try to access the appointment directly
    print(f"\n🔍 Testing direct appointment access for ID {appointment_id}...")
    direct_access_response = requests.get(f"{BASE_URL}/appointment/opd/{appointment_id}", 
                                        headers=headers, timeout=10)
    print(f"Direct access: {direct_access_response.status_code}")
    
    if direct_access_response.status_code != 200:
        print(f"Direct access failed: {direct_access_response.text}")
        response_data = direct_access_response.json() if direct_access_response.headers.get('content-type', '').startswith('application/json') else {}
        print(f"Error details: {response_data}")
    else:
        print("✅ Direct access successful!")
    
    # Step 5: Try to cancel the appointment
    print(f"\n❌ Testing appointment cancellation for ID {appointment_id}...")
    cancel_response = requests.delete(f"{BASE_URL}/appointment/opd/cancel/{appointment_id}", 
                                    headers=headers, timeout=10)
    print(f"Cancel appointment: {cancel_response.status_code}")
    
    if cancel_response.status_code != 200:
        print(f"Cancellation failed: {cancel_response.text}")
        response_data = cancel_response.json() if cancel_response.headers.get('content-type', '').startswith('application/json') else {}
        print(f"Error details: {response_data}")
    else:
        print("✅ Cancellation successful!")

if __name__ == "__main__":
    debug_appointment_access()