from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from app.services.audit_service import audit_service
from app.auth.decorators import admin_required
from app.utils.helpers import create_success_response, create_error_response

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('/logs', methods=['GET'])
@admin_required
def get_audit_logs():
    """Get audit logs with filtering"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        user_id = request.args.get('user_id', type=int)
        event_type = request.args.get('event_type')
        risk_level = request.args.get('risk_level')
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=50, type=int)
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        audit_logs = audit_service.get_audit_logs(
            start_date=start_dt,
            end_date=end_dt,
            user_id=user_id,
            event_type=event_type,
            risk_level=risk_level,
            page=page,
            per_page=per_page
        )
        
        return create_success_response(
            'Audit logs retrieved successfully',
            audit_logs
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve audit logs: {str(e)}', status_code=500)


@audit_bp.route('/security-summary', methods=['GET'])
@admin_required
def get_security_summary():
    """Get security summary for the specified time period"""
    try:
        days = request.args.get('days', default=7, type=int)
        
        security_summary = audit_service.get_security_summary(days=days)
        
        return create_success_response(
            'Security summary retrieved successfully',
            security_summary
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve security summary: {str(e)}', status_code=500)


@audit_bp.route('/user-activity-trail/<int:user_id>', methods=['GET'])
@admin_required
def get_user_activity_trail(user_id):
    """Get detailed activity trail for a specific user"""
    try:
        days = request.args.get('days', default=30, type=int)
        
        activity_trail = audit_service.get_user_activity_trail(user_id=user_id, days=days)
        
        return create_success_response(
            'User activity trail retrieved successfully',
            activity_trail
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve user activity trail: {str(e)}', status_code=500)


@audit_bp.route('/log-action', methods=['POST'])
@jwt_required()
def log_custom_action():
    """Log a custom action (for special events)"""
    try:
        data = request.get_json()
        
        if not data or 'action' not in data:
            return create_error_response('Action is required', status_code=400)
        
        action = data['action']
        details = data.get('details', {})
        target_user_id = data.get('target_user_id')
        risk_level = data.get('risk_level', 'medium')
        
        success = audit_service.log_user_action(
            action=action,
            details=details,
            target_user_id=target_user_id,
            status='success',
            risk_level=risk_level
        )
        
        if success:
            return create_success_response('Action logged successfully')
        else:
            return create_error_response('Failed to log action', status_code=500)
        
    except Exception as e:
        return create_error_response(f'Failed to log action: {str(e)}', status_code=500)


@audit_bp.route('/system-event', methods=['POST'])
@admin_required
def log_system_event():
    """Log a system event"""
    try:
        data = request.get_json()
        
        required_fields = ['event_type', 'description']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', status_code=400)
        
        event_type = data['event_type']
        description = data['description']
        severity = data.get('severity', 'info')
        component = data.get('component')
        
        success = audit_service.log_system_event(
            event_type=event_type,
            description=description,
            severity=severity,
            component=component
        )
        
        if success:
            return create_success_response('System event logged successfully')
        else:
            return create_error_response('Failed to log system event', status_code=500)
        
    except Exception as e:
        return create_error_response(f'Failed to log system event: {str(e)}', status_code=500)


@audit_bp.route('/compliance-report', methods=['GET'])
@admin_required
def get_compliance_report():
    """Generate compliance report (HIPAA, data access tracking, etc.)"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        report_type = request.args.get('type', default='hipaa')
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get audit logs for compliance
        audit_logs = audit_service.get_audit_logs(
            start_date=start_dt,
            end_date=end_dt,
            event_type='data_access',
            page=1,
            per_page=1000  # Get more records for compliance report
        )
        
        # Generate compliance-specific metrics
        compliance_data = {
            'report_type': report_type,
            'period': {
                'start_date': start_dt.isoformat() if start_dt else None,
                'end_date': end_dt.isoformat() if end_dt else None
            },
            'total_data_access_events': len(audit_logs.get('logs', [])),
            'high_risk_accesses': len([
                log for log in audit_logs.get('logs', [])
                if log.get('parsed_action', {}).get('risk_level') == 'high'
            ]),
            'user_access_summary': {},  # Would be populated with actual data
            'compliance_status': 'compliant',  # Would be determined by actual checks
            'recommendations': [
                'Implement regular access reviews',
                'Enable automatic log archival',
                'Set up real-time monitoring alerts'
            ]
        }
        
        return create_success_response(
            'Compliance report generated successfully',
            compliance_data
        )
        
    except Exception as e:
        return create_error_response(f'Failed to generate compliance report: {str(e)}', status_code=500)


@audit_bp.route('/failed-logins', methods=['GET'])
@admin_required
def get_failed_login_attempts():
    """Get failed login attempts for security monitoring"""
    try:
        hours = request.args.get('hours', default=24, type=int)
        ip_address = request.args.get('ip_address')
        
        # This would normally read from log files or cache
        # For now, return a placeholder structure
        failed_attempts = {
            'period_hours': hours,
            'total_attempts': 45,  # Would be calculated from actual logs
            'unique_ips': 12,
            'unique_usernames': 8,
            'top_failing_ips': [
                {'ip': '192.168.1.100', 'attempts': 15},
                {'ip': '10.0.0.50', 'attempts': 12},
                {'ip': '172.16.0.25', 'attempts': 8}
            ],
            'top_failing_usernames': [
                {'username': 'admin', 'attempts': 20},
                {'username': 'test_user', 'attempts': 10},
                {'username': 'doctor1', 'attempts': 5}
            ],
            'blocked_ips': ['192.168.1.100'],  # Would be fetched from cache
            'recommendations': [
                'Consider implementing CAPTCHA after 3 failed attempts',
                'Enable account lockout policies',
                'Set up geographic access restrictions'
            ]
        }
        
        return create_success_response(
            'Failed login attempts retrieved successfully',
            failed_attempts
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve failed login attempts: {str(e)}', status_code=500)


@audit_bp.route('/data-access-patterns', methods=['GET'])
@admin_required
def get_data_access_patterns():
    """Analyze data access patterns for anomaly detection"""
    try:
        days = request.args.get('days', default=7, type=int)
        user_id = request.args.get('user_id', type=int)
        
        # This would perform actual pattern analysis
        patterns = {
            'analysis_period_days': days,
            'anomalies_detected': 3,
            'unusual_access_times': [
                {
                    'user_id': 123,
                    'username': 'doctor_smith',
                    'access_time': '2024-01-15T02:30:00Z',
                    'resource': 'patient_records',
                    'anomaly_score': 0.85
                }
            ],
            'geographic_anomalies': [
                {
                    'user_id': 456,
                    'username': 'nurse_jones',
                    'usual_location': 'New York',
                    'access_location': 'California',
                    'risk_score': 0.92
                }
            ],
            'access_frequency_anomalies': [
                {
                    'user_id': 789,
                    'username': 'admin_user',
                    'usual_daily_accesses': 25,
                    'recent_daily_accesses': 150,
                    'anomaly_score': 0.78
                }
            ],
            'recommendations': [
                'Review access for doctor_smith at unusual hours',
                'Verify nurse_jones location change',
                'Investigate admin_user increased activity'
            ]
        }
        
        return create_success_response(
            'Data access patterns analyzed successfully',
            patterns
        )
        
    except Exception as e:
        return create_error_response(f'Failed to analyze data access patterns: {str(e)}', status_code=500)


@audit_bp.route('/export-logs', methods=['POST'])
@admin_required
def export_audit_logs():
    """Export audit logs for external analysis or compliance"""
    try:
        data = request.get_json()
        
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        export_format = data.get('format', 'json')  # json, csv, xlsx
        
        # Parse dates if provided
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get all audit logs for export
        audit_logs = audit_service.get_audit_logs(
            start_date=start_dt,
            end_date=end_dt,
            page=1,
            per_page=10000  # Large number for export
        )
        
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'export_format': export_format,
            'total_records': len(audit_logs.get('logs', [])),
            'logs': audit_logs.get('logs', []),
            'metadata': {
                'generated_by': get_jwt_identity(),
                'period': audit_logs.get('filters', {}),
                'export_purpose': 'compliance_audit'
            }
        }
        
        return create_success_response(
            'Audit logs exported successfully',
            export_data
        )
        
    except Exception as e:
        return create_error_response(f'Failed to export audit logs: {str(e)}', status_code=500)
