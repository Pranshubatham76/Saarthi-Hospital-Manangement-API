from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import db, Notification
from app.services.email_service import email_service
from app.services.websocket_service import websocket_service
from app.auth.decorators import admin_required
from app.utils.helpers import create_success_response, create_error_response, serialize_model
from app.services.cache_service import cache_service

notifications_bp = Blueprint('notifications', __name__)


@notifications_bp.route('/my-notifications', methods=['GET'])
@jwt_required()
def get_my_notifications():
    """Get notifications for current user"""
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=20, type=int)
        unread_only = request.args.get('unread_only', default=False, type=bool)
        
        query = Notification.query.filter_by(user_id=current_user_id)
        
        if unread_only:
            query = query.filter_by(read=False)
        
        query = query.order_by(Notification.created_at.desc())
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        notifications = []
        for notification in pagination.items:
            notifications.append(serialize_model(notification))
        
        return create_success_response(
            'Notifications retrieved successfully',
            {
                'notifications': notifications,
                'pagination': {
                    'page': pagination.page,
                    'pages': pagination.pages,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                }
            }
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve notifications: {str(e)}', status_code=500)


@notifications_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        current_user_id = get_jwt_identity()
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user_id
        ).first()
        
        if not notification:
            return create_error_response('Notification not found', status_code=404)
        
        notification.read = True
        db.session.commit()
        
        return create_success_response('Notification marked as read')
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Failed to mark notification as read: {str(e)}', status_code=500)


@notifications_bp.route('/mark-all-read', methods=['POST'])
@jwt_required()
def mark_all_notifications_read():
    """Mark all notifications as read for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        Notification.query.filter_by(
            user_id=current_user_id,
            read=False
        ).update({Notification.read: True})
        
        db.session.commit()
        
        return create_success_response('All notifications marked as read')
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Failed to mark all notifications as read: {str(e)}', status_code=500)


@notifications_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Get count of unread notifications for current user"""
    try:
        current_user_id = get_jwt_identity()
        
        # Try to get from cache first
        cache_key = f"unread_count:{current_user_id}"
        unread_count = cache_service.get(cache_key)
        
        if unread_count is None:
            unread_count = Notification.query.filter_by(
                user_id=current_user_id,
                read=False
            ).count()
            
            # Cache for 5 minutes
            cache_service.set(cache_key, unread_count, 300)
        
        return create_success_response(
            'Unread count retrieved successfully',
            {'unread_count': unread_count}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to get unread count: {str(e)}', status_code=500)


@notifications_bp.route('/send', methods=['POST'])
@admin_required
def send_notification():
    """Send notification to user(s)"""
    try:
        data = request.get_json()
        
        required_fields = ['title', 'body']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', status_code=400)
        
        title = data['title']
        body = data['body']
        user_ids = data.get('user_ids', [])  # List of user IDs
        send_email = data.get('send_email', False)
        send_websocket = data.get('send_websocket', True)
        metadata = data.get('metadata', {})
        
        if not user_ids:
            return create_error_response('At least one user ID is required', status_code=400)
        
        sent_count = 0
        failed_count = 0
        
        for user_id in user_ids:
            try:
                # Verify user exists before creating notification
                from app.models import Users
                user = Users.query.get(user_id)
                if not user:
                    failed_count += 1
                    continue
                
                # Create in-app notification
                notification = Notification(
                    user_id=user_id,
                    title=title,
                    body=body,
                    metadata=metadata,
                    read=False
                )
                db.session.add(notification)
                
                # Send WebSocket notification if requested
                if send_websocket and websocket_service:
                    websocket_service.emit_to_user(user_id, 'new_notification', {
                        'id': notification.id,
                        'title': title,
                        'body': body,
                        'metadata': metadata,
                        'created_at': notification.created_at.isoformat()
                    })
                
                # Send email notification if requested
                if send_email:
                    # User already fetched above
                    if user and user.email:
                        email_service.send_notification_and_email(
                            user_email=user.email,
                            user_id=user_id,
                            user_name=user.fullname,
                            subject=title,
                            email_body=body,
                            notification_metadata=metadata
                        )
                
                # Invalidate unread count cache
                cache_service.delete(f"unread_count:{user_id}")
                
                sent_count += 1
                
            except Exception as e:
                failed_count += 1
                continue
        
        db.session.commit()
        
        return create_success_response(
            f'Notifications sent successfully. Sent: {sent_count}, Failed: {failed_count}',
            {
                'sent_count': sent_count,
                'failed_count': failed_count,
                'total_requested': len(user_ids)
            }
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Failed to send notifications: {str(e)}', status_code=500)


@notifications_bp.route('/broadcast', methods=['POST'])
@admin_required
def broadcast_notification():
    """Broadcast notification to all users or users with specific roles"""
    try:
        data = request.get_json()
        
        required_fields = ['title', 'body']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', status_code=400)
        
        title = data['title']
        body = data['body']
        target_roles = data.get('target_roles', [])  # List of roles to target
        send_email = data.get('send_email', False)
        send_websocket = data.get('send_websocket', True)
        metadata = data.get('metadata', {})
        
        # Get target users
        from app.models import Users
        
        query = Users.query
        if target_roles:
            query = query.filter(Users.role.in_(target_roles))
        
        target_users = query.all()
        
        sent_count = 0
        failed_count = 0
        
        for user in target_users:
            try:
                # Create in-app notification
                notification = Notification(
                    user_id=user.id,
                    title=title,
                    body=body,
                    metadata=metadata,
                    read=False
                )
                db.session.add(notification)
                
                # Send WebSocket notification if requested
                if send_websocket and websocket_service:
                    websocket_service.emit_to_user(user.id, 'new_notification', {
                        'id': notification.id,
                        'title': title,
                        'body': body,
                        'metadata': metadata,
                        'created_at': notification.created_at.isoformat()
                    })
                
                # Send email notification if requested
                if send_email and user.email:
                    email_service.send_notification_and_email(
                        user_email=user.email,
                        user_id=user.id,
                        user_name=user.fullname,
                        subject=title,
                        email_body=body,
                        notification_metadata=metadata
                    )
                
                # Invalidate unread count cache
                cache_service.delete(f"unread_count:{user.id}")
                
                sent_count += 1
                
            except Exception as e:
                failed_count += 1
                continue
        
        db.session.commit()
        
        # Also send WebSocket system notification
        if send_websocket and websocket_service:
            websocket_service.emit_system_notification({
                'title': title,
                'body': body,
                'type': 'system_broadcast',
                'metadata': metadata
            })
        
        return create_success_response(
            f'Broadcast sent successfully. Sent: {sent_count}, Failed: {failed_count}',
            {
                'sent_count': sent_count,
                'failed_count': failed_count,
                'total_users': len(target_users),
                'target_roles': target_roles or 'all_users'
            }
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Failed to broadcast notification: {str(e)}', status_code=500)


@notifications_bp.route('/templates', methods=['GET'])
@admin_required
def get_notification_templates():
    """Get notification templates"""
    try:
        templates = [
            {
                'id': 'appointment_reminder',
                'name': 'Appointment Reminder',
                'title': 'Appointment Reminder - {appointment_date}',
                'body': 'You have an appointment scheduled for {appointment_date} with Dr. {doctor_name}. Please arrive 15 minutes early.',
                'category': 'appointments'
            },
            {
                'id': 'blood_request_approved',
                'name': 'Blood Request Approved',
                'title': 'Blood Request Approved',
                'body': 'Your blood request for {blood_type} has been approved. Please visit the blood bank to collect.',
                'category': 'blood_bank'
            },
            {
                'id': 'emergency_alert',
                'name': 'Emergency Alert',
                'title': 'Emergency Alert - {emergency_type}',
                'body': 'Emergency reported at {location}. Please respond immediately.',
                'category': 'emergency'
            },
            {
                'id': 'system_maintenance',
                'name': 'System Maintenance',
                'title': 'Scheduled System Maintenance',
                'body': 'The system will be under maintenance from {start_time} to {end_time}. Please save your work.',
                'category': 'system'
            },
            {
                'id': 'password_expiry',
                'name': 'Password Expiry Warning',
                'title': 'Password Expires Soon',
                'body': 'Your password will expire in {days} days. Please change it to maintain account security.',
                'category': 'security'
            }
        ]
        
        return create_success_response(
            'Notification templates retrieved successfully',
            {'templates': templates}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve templates: {str(e)}', status_code=500)


@notifications_bp.route('/send-template', methods=['POST'])
@admin_required
def send_template_notification():
    """Send notification using template"""
    try:
        data = request.get_json()
        
        required_fields = ['template_id', 'user_ids', 'variables']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', status_code=400)
        
        template_id = data['template_id']
        user_ids = data['user_ids']
        variables = data['variables']
        send_email = data.get('send_email', False)
        send_websocket = data.get('send_websocket', True)
        
        # Get template (this would normally be from database)
        templates = {
            'appointment_reminder': {
                'title': 'Appointment Reminder - {appointment_date}',
                'body': 'You have an appointment scheduled for {appointment_date} with Dr. {doctor_name}. Please arrive 15 minutes early.'
            },
            'blood_request_approved': {
                'title': 'Blood Request Approved',
                'body': 'Your blood request for {blood_type} has been approved. Please visit the blood bank to collect.'
            }
        }
        
        template = templates.get(template_id)
        if not template:
            return create_error_response('Template not found', status_code=404)
        
        # Format template with variables
        try:
            title = template['title'].format(**variables)
            body = template['body'].format(**variables)
        except KeyError as e:
            return create_error_response(f'Missing variable: {str(e)}', status_code=400)
        
        # Send notifications
        notification_data = {
            'title': title,
            'body': body,
            'user_ids': user_ids,
            'send_email': send_email,
            'send_websocket': send_websocket,
            'metadata': {
                'template_id': template_id,
                'variables': variables
            }
        }
        
        # Reuse the send_notification logic
        return send_notification()
        
    except Exception as e:
        return create_error_response(f'Failed to send template notification: {str(e)}', status_code=500)


@notifications_bp.route('/delete/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete_notification(notification_id):
    """Delete a notification"""
    try:
        current_user_id = get_jwt_identity()
        
        notification = Notification.query.filter_by(
            id=notification_id,
            user_id=current_user_id
        ).first()
        
        if not notification:
            return create_error_response('Notification not found', status_code=404)
        
        db.session.delete(notification)
        db.session.commit()
        
        # Invalidate unread count cache
        cache_service.delete(f"unread_count:{current_user_id}")
        
        return create_success_response('Notification deleted successfully')
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Failed to delete notification: {str(e)}', status_code=500)


@notifications_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_notification_settings():
    """Get user notification settings"""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user preferences (this would be from a UserPreferences table)
        settings = {
            'email_notifications': True,
            'websocket_notifications': True,
            'appointment_reminders': True,
            'emergency_alerts': True,
            'system_announcements': True,
            'blood_bank_updates': True,
            'quiet_hours': {
                'enabled': False,
                'start_time': '22:00',
                'end_time': '08:00'
            }
        }
        
        return create_success_response(
            'Notification settings retrieved successfully',
            {'settings': settings}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve notification settings: {str(e)}', status_code=500)


@notifications_bp.route('/settings', methods=['PUT'])
@jwt_required()
def update_notification_settings():
    """Update user notification settings"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate settings
        allowed_settings = [
            'email_notifications', 'websocket_notifications',
            'appointment_reminders', 'emergency_alerts',
            'system_announcements', 'blood_bank_updates'
        ]
        
        settings = {}
        for setting in allowed_settings:
            if setting in data:
                settings[setting] = bool(data[setting])
        
        if 'quiet_hours' in data:
            settings['quiet_hours'] = data['quiet_hours']
        
        # Store settings (this would normally go to UserPreferences table)
        cache_key = f"notification_settings:{current_user_id}"
        cache_service.set(cache_key, settings, 86400)  # Cache for 24 hours
        
        return create_success_response(
            'Notification settings updated successfully',
            {'settings': settings}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to update notification settings: {str(e)}', status_code=500)
