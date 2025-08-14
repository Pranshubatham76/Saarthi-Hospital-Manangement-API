from datetime import datetime, timedelta
from flask import request, current_app
from flask_jwt_extended import get_jwt_identity, get_jwt
import json
import os
import logging
from sqlalchemy import desc, and_, or_, func
from app.models import db, AdminLog, Users, Admin, Hospital_info
from app.utils.helpers import serialize_model, create_success_response, create_error_response


class AuditService:
    """Comprehensive audit logging and security monitoring service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def log_user_action(self, action, details=None, target_user_id=None, status='success', risk_level='low'):
        """Log user action with comprehensive details"""
        try:
            # Get current user info
            current_user_id = None
            user_type = 'unknown'
            user_role = 'unknown'
            
            try:
                current_user_id = get_jwt_identity()
                claims = get_jwt()
                user_type = claims.get('type', 'user')
                user_role = claims.get('role', 'user')
            except:
                pass
            
            # Get request details
            ip_address = self._get_client_ip()
            user_agent = request.headers.get('User-Agent', '')
            endpoint = request.endpoint or 'unknown'
            method = request.method
            
            # Create comprehensive log entry
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': current_user_id,
                'user_type': user_type,
                'user_role': user_role,
                'action': action,
                'endpoint': endpoint,
                'method': method,
                'target_user_id': target_user_id,
                'status': status,
                'risk_level': risk_level,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'details': details or {},
                'session_id': self._get_session_id()
            }
            
            # Store in database
            if user_type == 'admin' and current_user_id:
                admin_log = AdminLog(
                    admin_id=current_user_id,
                    user_id=target_user_id,
                    action=json.dumps(log_entry)
                )
                db.session.add(admin_log)
                db.session.commit()
            
            # Log to file system
            self._log_to_file(log_entry)
            
            # Check for suspicious activity
            self._check_suspicious_activity(log_entry)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging user action: {str(e)}")
            return False
    
    def log_login_attempt(self, username, success=True, failure_reason=None):
        """Log login attempts with security monitoring"""
        try:
            ip_address = self._get_client_ip()
            user_agent = request.headers.get('User-Agent', '')
            
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': 'login_attempt',
                'username': username,
                'success': success,
                'failure_reason': failure_reason,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'risk_level': 'high' if not success else 'medium'
            }
            
            # Store in database
            try:
                # Try to find user for additional context
                user = Users.query.filter_by(username=username).first()
                admin = Admin.query.filter_by(username=username).first()
                hospital = Hospital_info.query.filter_by(username=username).first()
                
                target_id = None
                if user:
                    target_id = user.id
                    log_entry['user_type'] = 'user'
                elif admin:
                    target_id = admin.id
                    log_entry['user_type'] = 'admin'
                elif hospital:
                    target_id = hospital.id
                    log_entry['user_type'] = 'hospital'
                
                if admin and success:
                    admin_log = AdminLog(
                        admin_id=target_id,
                        user_id=None,
                        action=json.dumps(log_entry)
                    )
                    db.session.add(admin_log)
                    db.session.commit()
                
            except Exception as db_error:
                self.logger.warning(f"Could not store login attempt in database: {str(db_error)}")
            
            # Log to file system
            self._log_to_file(log_entry)
            
            # Check for brute force attempts
            if not success:
                self._check_brute_force_attempt(username, ip_address)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging login attempt: {str(e)}")
            return False
    
    def log_data_access(self, resource_type, resource_id, access_type='read'):
        """Log data access for HIPAA/privacy compliance"""
        try:
            current_user_id = get_jwt_identity()
            claims = get_jwt()
            user_role = claims.get('role', 'user')
            
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': 'data_access',
                'user_id': current_user_id,
                'user_role': user_role,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'access_type': access_type,
                'ip_address': self._get_client_ip(),
                'user_agent': request.headers.get('User-Agent', ''),
                'endpoint': request.endpoint,
                'risk_level': self._assess_data_access_risk(resource_type, access_type, user_role)
            }
            
            # Log to file system (important for compliance)
            self._log_to_file(log_entry)
            
            # Check for unauthorized access patterns
            self._check_unauthorized_access(log_entry)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging data access: {str(e)}")
            return False
    
    def log_system_event(self, event_type, description, severity='info', component=None):
        """Log system events and errors"""
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': 'system_event',
                'system_event_type': event_type,
                'description': description,
                'severity': severity,
                'component': component,
                'server_info': {
                    'host': request.host,
                    'url': request.url,
                    'method': request.method
                }
            }
            
            # Log to file system
            self._log_to_file(log_entry)
            
            # Alert for high severity events
            if severity in ['error', 'critical']:
                self._alert_system_administrators(log_entry)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging system event: {str(e)}")
            return False
    
    def get_audit_logs(self, start_date=None, end_date=None, user_id=None, event_type=None, 
                       risk_level=None, page=1, per_page=50):
        """Retrieve audit logs with filtering"""
        try:
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Build query
            query = AdminLog.query.filter(
                AdminLog.timestamp >= start_date,
                AdminLog.timestamp <= end_date
            )
            
            if user_id:
                query = query.filter(
                    or_(AdminLog.admin_id == user_id, AdminLog.user_id == user_id)
                )
            
            # Order by timestamp (newest first)
            query = query.order_by(desc(AdminLog.timestamp))
            
            # Paginate
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            logs = []
            for log in pagination.items:
                log_data = serialize_model(log)
                
                # Parse action JSON if present
                try:
                    if log.action:
                        action_data = json.loads(log.action)
                        log_data['parsed_action'] = action_data
                except json.JSONDecodeError:
                    log_data['parsed_action'] = None
                
                # Add related user information
                if log.admin:
                    log_data['admin'] = serialize_model(log.admin, exclude=['password'])
                if log.user:
                    log_data['user'] = serialize_model(log.user, exclude=['password'])
                
                logs.append(log_data)
            
            return {
                'logs': logs,
                'pagination': {
                    'page': pagination.page,
                    'pages': pagination.pages,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev
                },
                'filters': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'user_id': user_id,
                    'event_type': event_type,
                    'risk_level': risk_level
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error retrieving audit logs: {str(e)}")
            raise
    
    def get_security_summary(self, days=7):
        """Get security summary for the specified time period"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Count various security events
            total_logs = AdminLog.query.filter(
                AdminLog.timestamp >= start_date,
                AdminLog.timestamp <= end_date
            ).count()
            
            # Get login attempt statistics from file logs
            login_stats = self._get_login_statistics(start_date, end_date)
            
            # Get risk level distribution
            risk_distribution = self._get_risk_distribution(start_date, end_date)
            
            # Get top users by activity
            top_users = self._get_top_users_by_activity(start_date, end_date)
            
            # Get suspicious activity alerts
            suspicious_activities = self._get_suspicious_activities(start_date, end_date)
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'summary': {
                    'total_audit_logs': total_logs,
                    'login_attempts': login_stats,
                    'risk_distribution': risk_distribution,
                    'top_active_users': top_users,
                    'suspicious_activities_count': len(suspicious_activities),
                    'suspicious_activities': suspicious_activities[:10]  # Top 10
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating security summary: {str(e)}")
            raise
    
    def get_user_activity_trail(self, user_id, days=30):
        """Get detailed activity trail for a specific user"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get audit logs for this user
            user_logs = AdminLog.query.filter(
                or_(AdminLog.admin_id == user_id, AdminLog.user_id == user_id),
                AdminLog.timestamp >= start_date,
                AdminLog.timestamp <= end_date
            ).order_by(desc(AdminLog.timestamp)).all()
            
            activities = []
            for log in user_logs:
                activity = serialize_model(log)
                
                # Parse action data
                try:
                    if log.action:
                        action_data = json.loads(log.action)
                        activity['parsed_action'] = action_data
                except json.JSONDecodeError:
                    activity['parsed_action'] = None
                
                activities.append(activity)
            
            # Get user information
            user_info = None
            user = Users.query.get(user_id)
            admin = Admin.query.get(user_id)
            hospital = Hospital_info.query.get(user_id)
            
            if user:
                user_info = serialize_model(user, exclude=['password'])
                user_info['type'] = 'user'
            elif admin:
                user_info = serialize_model(admin, exclude=['password'])
                user_info['type'] = 'admin'
            elif hospital:
                user_info = serialize_model(hospital, exclude=['password'])
                user_info['type'] = 'hospital'
            
            return {
                'user_info': user_info,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': days
                },
                'total_activities': len(activities),
                'activities': activities
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user activity trail: {str(e)}")
            raise
    
    def _get_client_ip(self):
        """Get client IP address considering proxies"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'
    
    def _get_session_id(self):
        """Get or generate session ID"""
        try:
            claims = get_jwt()
            return claims.get('jti', 'unknown')
        except:
            return 'unknown'
    
    def _log_to_file(self, log_entry):
        """Log entry to file system"""
        try:
            # Create logs directory if it doesn't exist
            logs_dir = current_app.config.get('LOGS_DIR', 'logs')
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            
            # Create log file name based on date and event type
            today = datetime.utcnow().strftime('%Y-%m-%d')
            event_type = log_entry.get('event_type', 'general')
            log_file = os.path.join(logs_dir, f'audit_{event_type}_{today}.log')
            
            # Write log entry
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            self.logger.error(f"Error writing to log file: {str(e)}")
    
    def _assess_data_access_risk(self, resource_type, access_type, user_role):
        """Assess risk level of data access"""
        high_risk_resources = ['prescription', 'visit', 'emergency', 'blood_requests']
        sensitive_operations = ['delete', 'update']
        
        if resource_type in high_risk_resources:
            if access_type in sensitive_operations:
                return 'high'
            return 'medium'
        
        if access_type in sensitive_operations:
            return 'medium'
        
        return 'low'
    
    def _check_suspicious_activity(self, log_entry):
        """Check for suspicious activity patterns"""
        try:
            user_id = log_entry.get('user_id')
            ip_address = log_entry.get('ip_address')
            action = log_entry.get('action')
            
            # Check for unusual activity patterns
            suspicious_flags = []
            
            # Multiple failed actions in short time
            if log_entry.get('status') == 'failure':
                recent_failures = self._count_recent_failures(user_id, ip_address)
                if recent_failures >= 5:
                    suspicious_flags.append('multiple_failures')
            
            # Access from new IP
            if self._is_new_ip_for_user(user_id, ip_address):
                suspicious_flags.append('new_ip_access')
            
            # High-risk actions
            high_risk_actions = ['delete_user', 'update_role', 'access_admin_panel']
            if action in high_risk_actions:
                suspicious_flags.append('high_risk_action')
            
            # Log suspicious activity
            if suspicious_flags:
                self._alert_suspicious_activity(log_entry, suspicious_flags)
                
        except Exception as e:
            self.logger.error(f"Error checking suspicious activity: {str(e)}")
    
    def _check_brute_force_attempt(self, username, ip_address):
        """Check for brute force login attempts"""
        try:
            # Count failed attempts in last 15 minutes
            threshold_time = datetime.utcnow() - timedelta(minutes=15)
            
            # This would typically check log files or a cache like Redis
            # For now, we'll log the potential brute force attempt
            self.logger.warning(f"Potential brute force attempt: {username} from {ip_address}")
            
            # In a real implementation, you would:
            # 1. Temporarily lock the account
            # 2. Add IP to temporary blacklist
            # 3. Send alert to administrators
            
        except Exception as e:
            self.logger.error(f"Error checking brute force attempt: {str(e)}")
    
    def _check_unauthorized_access(self, log_entry):
        """Check for unauthorized data access patterns"""
        try:
            user_role = log_entry.get('user_role')
            resource_type = log_entry.get('resource_type')
            
            # Define role-based access rules
            unauthorized_access = False
            
            if user_role == 'user' and resource_type in ['admin_logs', 'system_config']:
                unauthorized_access = True
            elif user_role == 'doctor' and resource_type in ['blood_bank_admin', 'hospital_admin']:
                unauthorized_access = True
            
            if unauthorized_access:
                self.logger.warning(f"Unauthorized access attempt: {user_role} accessing {resource_type}")
                self._alert_unauthorized_access(log_entry)
                
        except Exception as e:
            self.logger.error(f"Error checking unauthorized access: {str(e)}")
    
    def _alert_system_administrators(self, log_entry):
        """Alert system administrators of critical events"""
        try:
            # This would integrate with email service or notification system
            self.logger.critical(f"ALERT: {log_entry.get('description', 'System event')}")
            
            # In a real implementation:
            # 1. Send email alerts
            # 2. Create dashboard notifications
            # 3. Integrate with monitoring systems (PagerDuty, Slack, etc.)
            
        except Exception as e:
            self.logger.error(f"Error alerting administrators: {str(e)}")
    
    def _alert_suspicious_activity(self, log_entry, flags):
        """Alert about suspicious activity"""
        try:
            alert_message = f"Suspicious activity detected: {', '.join(flags)}"
            self.logger.warning(f"{alert_message} - User: {log_entry.get('user_id')}, IP: {log_entry.get('ip_address')}")
            
        except Exception as e:
            self.logger.error(f"Error alerting suspicious activity: {str(e)}")
    
    def _alert_unauthorized_access(self, log_entry):
        """Alert about unauthorized access attempts"""
        try:
            self.logger.warning(f"Unauthorized access: {log_entry.get('user_role')} -> {log_entry.get('resource_type')}")
            
        except Exception as e:
            self.logger.error(f"Error alerting unauthorized access: {str(e)}")
    
    def _count_recent_failures(self, user_id, ip_address, minutes=15):
        """Count recent failures for user/IP (placeholder implementation)"""
        # In a real implementation, this would check log files or Redis cache
        return 0
    
    def _is_new_ip_for_user(self, user_id, ip_address):
        """Check if this is a new IP for the user (placeholder implementation)"""
        # In a real implementation, this would check historical IP addresses
        return False
    
    def _get_login_statistics(self, start_date, end_date):
        """Get login statistics from logs (placeholder implementation)"""
        return {
            'total_attempts': 0,
            'successful_logins': 0,
            'failed_logins': 0,
            'unique_users': 0
        }
    
    def _get_risk_distribution(self, start_date, end_date):
        """Get risk level distribution (placeholder implementation)"""
        return {
            'low': 0,
            'medium': 0,
            'high': 0
        }
    
    def _get_top_users_by_activity(self, start_date, end_date):
        """Get top users by activity"""
        try:
            # Query top active users
            top_users = db.session.query(
                AdminLog.admin_id,
                func.count(AdminLog.id).label('activity_count')
            ).filter(
                AdminLog.timestamp >= start_date,
                AdminLog.timestamp <= end_date,
                AdminLog.admin_id.isnot(None)
            ).group_by(AdminLog.admin_id).order_by(
                desc(func.count(AdminLog.id))
            ).limit(10).all()
            
            result = []
            for user_activity in top_users:
                admin = Admin.query.get(user_activity.admin_id)
                if admin:
                    result.append({
                        'user_id': admin.id,
                        'username': admin.username,
                        'activity_count': user_activity.activity_count
                    })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting top users by activity: {str(e)}")
            return []
    
    def _get_suspicious_activities(self, start_date, end_date):
        """Get suspicious activities (placeholder implementation)"""
        return []


# Global audit service instance
audit_service = AuditService()
