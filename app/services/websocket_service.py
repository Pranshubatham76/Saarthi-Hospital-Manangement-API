from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from flask_jwt_extended import decode_token
from flask import current_app
import json
import logging
from datetime import datetime
from app.models import Users, Admin, Hospital_info
import redis
import threading
import time


class WebSocketService:
    """Real-time WebSocket service for live updates"""
    
    def __init__(self):
        self.socketio = None
        self.redis_client = None
        self.connected_users = {}  # Format: {socket_id: {user_id, role, rooms}}
        self.logger = logging.getLogger(__name__)
    
    def init_app(self, app, socketio):
        """Initialize WebSocket service with Flask app and SocketIO"""
        self.socketio = socketio
        
        # Initialize Redis for pub/sub if available
        try:
            redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()  # Test connection
            self.logger.info("Redis connected for WebSocket pub/sub")
        except Exception as e:
            self.logger.warning(f"Redis not available for WebSocket: {str(e)}")
            self.redis_client = None
        
        self._register_handlers()
    
    def _register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def on_connect(auth):
            """Handle client connection"""
            try:
                # Extract JWT token from auth
                if auth and 'token' in auth:
                    token_data = decode_token(auth['token'])
                    user_id = token_data['sub']
                    claims = token_data.get('claims', {})
                    user_role = claims.get('role', 'user')
                    user_type = claims.get('type', 'user')
                    
                    # Store connection info
                    from flask import request
                    socket_id = request.sid
                    self.connected_users[socket_id] = {
                        'user_id': user_id,
                        'role': user_role,
                        'type': user_type,
                        'rooms': set(),
                        'connected_at': datetime.utcnow()
                    }
                    
                    # Join user to their personal room
                    personal_room = f"user_{user_id}"
                    join_room(personal_room)
                    self.connected_users[socket_id]['rooms'].add(personal_room)
                    
                    # Join role-based rooms
                    role_room = f"role_{user_role}"
                    join_room(role_room)
                    self.connected_users[socket_id]['rooms'].add(role_room)
                    
                    # If hospital admin, join hospital room
                    if user_type == 'hospital':
                        hospital_room = f"hospital_{user_id}"
                        join_room(hospital_room)
                        self.connected_users[socket_id]['rooms'].add(hospital_room)
                    
                    self.logger.info(f"User {user_id} connected via WebSocket")
                    emit('connected', {'status': 'success', 'message': 'Connected successfully'})
                    
                    # Send any pending notifications
                    self._send_pending_notifications(user_id)
                    
                else:
                    emit('error', {'message': 'Authentication required'})
                    return False
                    
            except Exception as e:
                self.logger.error(f"Connection error: {str(e)}")
                emit('error', {'message': 'Authentication failed'})
                return False
        
        @self.socketio.on('disconnect')
        def on_disconnect():
            """Handle client disconnection"""
            from flask import request
            socket_id = request.sid
            
            if socket_id in self.connected_users:
                user_info = self.connected_users[socket_id]
                user_id = user_info['user_id']
                
                # Leave all rooms
                for room in user_info['rooms']:
                    leave_room(room)
                
                del self.connected_users[socket_id]
                self.logger.info(f"User {user_id} disconnected from WebSocket")
        
        @self.socketio.on('join_room')
        def on_join_room(data):
            """Handle room join requests"""
            from flask import request
            socket_id = request.sid
            
            if socket_id not in self.connected_users:
                emit('error', {'message': 'Not authenticated'})
                return
            
            user_info = self.connected_users[socket_id]
            room_name = data.get('room')
            
            if self._can_join_room(user_info, room_name):
                join_room(room_name)
                user_info['rooms'].add(room_name)
                emit('room_joined', {'room': room_name})
                self.logger.info(f"User {user_info['user_id']} joined room {room_name}")
            else:
                emit('error', {'message': 'Access denied to room'})
        
        @self.socketio.on('leave_room')
        def on_leave_room(data):
            """Handle room leave requests"""
            from flask import request
            socket_id = request.sid
            
            if socket_id not in self.connected_users:
                return
            
            user_info = self.connected_users[socket_id]
            room_name = data.get('room')
            
            if room_name in user_info['rooms']:
                leave_room(room_name)
                user_info['rooms'].discard(room_name)
                emit('room_left', {'room': room_name})
        
        @self.socketio.on('ping')
        def on_ping():
            """Handle ping for connection health check"""
            emit('pong', {'timestamp': datetime.utcnow().isoformat()})
    
    def _can_join_room(self, user_info, room_name):
        """Check if user can join a specific room"""
        user_role = user_info['role']
        user_id = user_info['user_id']
        
        # Admin can join any room
        if user_role == 'admin':
            return True
        
        # Personal rooms
        if room_name == f"user_{user_id}":
            return True
        
        # Role-based rooms
        if room_name == f"role_{user_role}":
            return True
        
        # Hospital rooms (for hospital admins)
        if room_name.startswith('hospital_') and user_info['type'] == 'hospital':
            return True
        
        # Emergency rooms (for emergency services)
        if room_name.startswith('emergency_') and user_role in ['admin', 'ambulance_driver']:
            return True
        
        # Appointment rooms (for doctors and patients)
        if room_name.startswith('appointment_') and user_role in ['doctor', 'user', 'admin']:
            return True
        
        return False
    
    def _send_pending_notifications(self, user_id):
        """Send pending notifications to newly connected user"""
        try:
            from app.models import Notification
            
            # Get unread notifications
            notifications = Notification.query.filter_by(
                user_id=user_id,
                read=False
            ).order_by(Notification.created_at.desc()).limit(10).all()
            
            if notifications:
                notification_data = []
                for notification in notifications:
                    notification_data.append({
                        'id': notification.id,
                        'title': notification.title,
                        'body': notification.body,
                        'metadata': notification.metadata,
                        'created_at': notification.created_at.isoformat()
                    })
                
                self.emit_to_user(user_id, 'pending_notifications', {
                    'notifications': notification_data
                })
                
        except Exception as e:
            self.logger.error(f"Error sending pending notifications: {str(e)}")
    
    def emit_to_user(self, user_id, event, data):
        """Emit event to a specific user"""
        room = f"user_{user_id}"
        self.socketio.emit(event, data, room=room)
        self.logger.debug(f"Emitted {event} to user {user_id}")
    
    def emit_to_role(self, role, event, data):
        """Emit event to all users with a specific role"""
        room = f"role_{role}"
        self.socketio.emit(event, data, room=room)
        self.logger.debug(f"Emitted {event} to role {role}")
    
    def emit_to_hospital(self, hospital_id, event, data):
        """Emit event to a specific hospital"""
        room = f"hospital_{hospital_id}"
        self.socketio.emit(event, data, room=room)
        self.logger.debug(f"Emitted {event} to hospital {hospital_id}")
    
    def emit_emergency_alert(self, emergency_data):
        """Emit emergency alert to relevant users"""
        # Send to all admins
        self.emit_to_role('admin', 'emergency_alert', emergency_data)
        
        # Send to hospital if specified
        if emergency_data.get('hospital_id'):
            self.emit_to_hospital(emergency_data['hospital_id'], 'emergency_alert', emergency_data)
        
        # Send to ambulance drivers
        self.emit_to_role('ambulance_driver', 'emergency_alert', emergency_data)
        
        self.logger.info(f"Emergency alert broadcasted for emergency {emergency_data.get('id')}")
    
    def emit_appointment_update(self, appointment_data):
        """Emit appointment update to relevant users"""
        patient_id = appointment_data.get('patient_id')
        doctor_id = appointment_data.get('doctor_id')
        hospital_id = appointment_data.get('hospital_id')
        
        # Notify patient
        if patient_id:
            self.emit_to_user(patient_id, 'appointment_update', appointment_data)
        
        # Notify doctor
        if doctor_id:
            self.emit_to_user(doctor_id, 'appointment_update', appointment_data)
        
        # Notify hospital
        if hospital_id:
            self.emit_to_hospital(hospital_id, 'appointment_update', appointment_data)
        
        # Notify admins
        self.emit_to_role('admin', 'appointment_update', appointment_data)
        
        self.logger.info(f"Appointment update broadcasted for appointment {appointment_data.get('id')}")
    
    def emit_bed_status_update(self, bed_data):
        """Emit bed status update to hospital personnel"""
        hospital_id = bed_data.get('hospital_id')
        
        if hospital_id:
            # Notify hospital
            self.emit_to_hospital(hospital_id, 'bed_status_update', bed_data)
            
            # Notify admins
            self.emit_to_role('admin', 'bed_status_update', bed_data)
            
            self.logger.info(f"Bed status update broadcasted for hospital {hospital_id}")
    
    def emit_blood_stock_alert(self, blood_data):
        """Emit blood stock alert to relevant users"""
        # Notify admins
        self.emit_to_role('admin', 'blood_stock_alert', blood_data)
        
        # Notify hospital admins
        self.emit_to_role('hospital_admin', 'blood_stock_alert', blood_data)
        
        self.logger.info(f"Blood stock alert broadcasted for blood bank {blood_data.get('bloodbank_id')}")
    
    def emit_system_notification(self, notification_data):
        """Emit system-wide notification"""
        # Broadcast to all connected users
        self.socketio.emit('system_notification', notification_data, broadcast=True)
        self.logger.info("System notification broadcasted to all users")
    
    def get_connected_users_count(self):
        """Get count of connected users"""
        return len(self.connected_users)
    
    def get_connected_users_by_role(self):
        """Get connected users grouped by role"""
        role_counts = {}
        for user_info in self.connected_users.values():
            role = user_info['role']
            role_counts[role] = role_counts.get(role, 0) + 1
        return role_counts
    
    def broadcast_system_stats(self):
        """Broadcast system statistics to admins"""
        try:
            from app.models import Hospital, Users, Appointment, Emergency
            
            stats = {
                'connected_users': self.get_connected_users_count(),
                'users_by_role': self.get_connected_users_by_role(),
                'total_hospitals': Hospital.query.count(),
                'total_users': Users.query.count(),
                'active_appointments': Appointment.query.filter_by(status='confirmed').count(),
                'pending_emergencies': Emergency.query.filter_by(forward_status='Pending').count(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.emit_to_role('admin', 'system_stats', stats)
            
        except Exception as e:
            self.logger.error(f"Error broadcasting system stats: {str(e)}")
    
    def start_background_tasks(self):
        """Start background tasks for periodic updates"""
        def stats_broadcaster():
            while True:
                try:
                    time.sleep(30)  # Every 30 seconds
                    self.broadcast_system_stats()
                except Exception as e:
                    self.logger.error(f"Stats broadcaster error: {str(e)}")
        
        # Start background thread
        stats_thread = threading.Thread(target=stats_broadcaster, daemon=True)
        stats_thread.start()
        self.logger.info("Background WebSocket tasks started")


# Global WebSocket service instance
websocket_service = WebSocketService()


def init_websocket_service(app, socketio):
    """Initialize WebSocket service"""
    websocket_service.init_app(app, socketio)
    return websocket_service
