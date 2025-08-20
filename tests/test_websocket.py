#!/usr/bin/env python3
"""
Test WebSocket functionality
"""
import socketio
import time
import threading
import requests
import json

# Standard SocketIO Client
sio = socketio.Client()

@sio.event
def connect():
    print("✅ WebSocket connected to server")

@sio.event
def disconnect():
    print("❌ WebSocket disconnected from server")

@sio.event
def connect_error(data):
    print(f"❌ WebSocket connection error: {data}")

@sio.on('notification')
def on_notification(data):
    print(f"📢 Received notification: {data}")

@sio.on('emergency_alert')
def on_emergency_alert(data):
    print(f"🚨 Emergency alert received: {data}")

@sio.on('bed_status_update')
def on_bed_status_update(data):
    print(f"🛏️  Bed status update: {data}")

@sio.on('appointment_update')
def on_appointment_update(data):
    print(f"📅 Appointment update: {data}")

def test_websocket_connection():
    """Test basic WebSocket connection"""
    print("=== Testing WebSocket Connection ===")
    
    try:
        # Connect to the WebSocket server
        sio.connect('http://localhost:5000')
        print("Connected successfully!")
        
        # Test emitting some events
        print("\n=== Testing Event Emission ===")
        
        # Emit a test join room event
        sio.emit('join', {'room': 'hospital_1'})
        print("✅ Emitted 'join' event")
        
        # Keep connection alive for a few seconds to receive any messages
        time.sleep(2)
        
        # Test notification emission
        sio.emit('test_notification', {'message': 'Test notification from client'})
        print("✅ Emitted 'test_notification' event")
        
        time.sleep(2)
        
        # Disconnect
        sio.disconnect()
        print("✅ WebSocket disconnected cleanly")
        
        return True
        
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

def test_websocket_endpoints():
    """Test WebSocket-related API endpoints"""
    print("\n=== Testing WebSocket API Endpoints ===")
    
    # Test sending a notification via API
    try:
        # Get admin token first
        admin_response = requests.post(
            'http://localhost:5000/auth/admin/login',
            json={'username': 'admin@hospital.com', 'password': 'admin123'},
            headers={'Content-Type': 'application/json'}
        )
        
        if admin_response.status_code == 200:
            admin_token = admin_response.json()['data']['access_token']
            
            # Test sending notification
            notification_response = requests.post(
                'http://localhost:5000/notifications/send',
                json={
                    'recipient_type': 'hospital',
                    'recipient_id': 1,
                    'title': 'Test Notification',
                    'message': 'This is a test WebSocket notification',
                    'notification_type': 'info'
                },
                headers={
                    'Authorization': f'Bearer {admin_token}',
                    'Content-Type': 'application/json'
                }
            )
            
            print(f"Notification API Status: {notification_response.status_code}")
            if notification_response.status_code == 201:
                print("✅ Notification sent successfully via API")
                print(f"Response: {notification_response.json()}")
            else:
                print(f"❌ Notification API failed: {notification_response.text}")
                
        else:
            print(f"❌ Admin login failed: {admin_response.status_code}")
            
    except Exception as e:
        print(f"❌ WebSocket API test failed: {e}")

def test_emergency_websocket():
    """Test emergency WebSocket notifications"""
    print("\n=== Testing Emergency WebSocket Integration ===")
    
    try:
        # Create an emergency call which should trigger WebSocket notification
        emergency_response = requests.post(
            'http://localhost:5000/emergency/call',
            json={
                'emergency_type': 'Medical',
                'location': '123 Test Street',
                'contact_number': '555-TEST',
                'details': 'WebSocket test emergency'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Emergency call status: {emergency_response.status_code}")
        if emergency_response.status_code == 201:
            print("✅ Emergency call created successfully")
            emergency_data = emergency_response.json()
            print(f"Emergency ID: {emergency_data['data']['emergency']['id']}")
        else:
            print(f"❌ Emergency call failed: {emergency_response.text}")
            
    except Exception as e:
        print(f"❌ Emergency WebSocket test failed: {e}")

if __name__ == '__main__':
    print("🔌 WebSocket Functionality Testing")
    print("====================================")
    
    # Start WebSocket connection in a separate thread
    websocket_thread = threading.Thread(target=test_websocket_connection)
    websocket_thread.daemon = True
    websocket_thread.start()
    
    # Wait a moment for connection
    time.sleep(1)
    
    # Test API endpoints
    test_websocket_endpoints()
    
    # Test emergency integration
    test_emergency_websocket()
    
    # Wait for WebSocket thread to complete
    websocket_thread.join(timeout=10)
    
    print("\n🏁 WebSocket testing completed!")