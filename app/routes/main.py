from flask import Blueprint, jsonify, request
from app.models import Hospital, BloodBank
from app.utils.helpers import serialize_model, create_success_response, create_error_response

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def api_welcome():
    """API Welcome endpoint"""
    return create_success_response(
        'Welcome to Hospital Management System API',
        {
            'name': 'Hospital Management System API',
            'version': '1.0.0',
            'description': 'RESTful API for complete hospital management system',
            'documentation': '/api/info',
            'interactive_docs': '/api-docs',
            'swagger_ui': '/swagger',
            'swagger_json': '/swagger.json',
            'health_check': '/health'
        }
    )


@main_bp.route('/contact', methods=['POST'])
def contact_api():
    """Contact form API endpoint"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'email', 'message']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', status_code=400)
        
        # Here you could save to database or send email
        # For now, we'll just return success response
        contact_data = {
            'name': data['name'],
            'email': data['email'],
            'message': data['message'],
            'submitted_at': str(request.remote_addr)
        }
        
        return create_success_response(
            'Contact form submitted successfully',
            contact_data,
            status_code=201
        )
        
    except Exception as e:
        return create_error_response(f'Contact form submission failed: {str(e)}', status_code=500)


@main_bp.route('/api/info')
def api_info():
    """API information"""
    return create_success_response(
        'Hospital Management System API Information',
        {
            'name': 'Hospital Management System',
            'version': '1.0.0',
            'description': 'Complete hospital management system with JWT authentication and RBAC',
            'features': [
                'User Management with Role-Based Access Control',
                'Hospital Registration and Management',
                'Multi-level Hospital Support (Floors, Wards, Beds)',
                'Doctor Scheduling and Appointment Booking',
                'OPD Slot Management',
                'Blood Bank Management',
                'Emergency Services',
                'Admin Dashboard',
                'JWT Authentication',
                'RESTful API Design',
                'Real-time WebSocket Communication',
                'Advanced Rate Limiting & API Protection',
                'Comprehensive Audit Logging & Security Monitoring',
                'Detailed Reporting & Analytics',
                'Email Notifications & Templates',
                'Redis Caching & Session Management'
            ],
            'endpoints': {
                'auth': {
                    'register': 'POST /auth/register',
                    'login': 'POST /auth/login',
                    'admin_login': 'POST /auth/admin/login',
                    'hospital_login': 'POST /auth/hospital/login',
                    'refresh': 'POST /auth/refresh',
                    'logout': 'POST /auth/logout',
                    'profile': 'GET /auth/profile',
                    'change_password': 'POST /auth/change-password'
                },
                'users': {
                    'update_profile': 'PUT /user/profile/update',
                    'get_all': 'GET /user/all',
                    'get_user': 'GET /user/<id>',
                    'delete_user': 'DELETE /user/delete/<id>',
                    'update_role': 'PUT /user/update-role/<id>',
                    'search': 'GET /user/search',
                    'stats': 'GET /user/stats'
                },
                'hospitals': {
                    'register': 'POST /hospital/register',
                    'get_all': 'GET /hospital/all',
                    'get_hospital': 'GET /hospital/<id>',
                    'update': 'PUT /hospital/update/<id>',
                    'delete': 'DELETE /hospital/delete/<id>',
                    'floors': 'GET /hospital/<id>/floors',
                    'create_floor': 'POST /hospital/<id>/floors/create',
                    'wards': 'GET /hospital/<id>/wards',
                    'create_ward': 'POST /hospital/ward/create',
                    'beds': 'GET /hospital/ward/<id>/beds',
                    'create_bed': 'POST /hospital/ward/<id>/bed/create'
                },
                'appointments': {
                    'book_opd': 'POST /appointment/opd/book',
                    'get_appointment': 'GET /appointment/opd/<id>',
                    'update': 'PUT /appointment/opd/update/<id>',
                    'cancel': 'DELETE /appointment/opd/cancel/<id>',
                    'my_appointments': 'GET /appointment/my-appointments',
                    'hospital_appointments': 'GET /appointment/hospital/<id>/appointments',
                    'available_slots': 'GET /appointment/available-slots'
                },
                'blood_bank': {
                    'register': 'POST /bloodbank/register',
                    'get_all': 'GET /bloodbank/all',
                    'add_stock': 'POST /bloodbank/<id>/addstock',
                    'get_stock': 'GET /bloodbank/<id>/stock',
                    'request_blood': 'POST /bloodbank/request',
                    'get_requests': 'GET /bloodbank/requests'
                },
                'emergency': {
                    'log_emergency': 'POST /emergency/call',
                    'get_all': 'GET /emergency/all',
                    'update': 'PUT /emergency/update/<id>',
                    'available_ambulances': 'GET /emergency/ambulances/available'
                },
                'admin': {
                    'create_admin': 'POST /admin/create',
                    'dashboard_stats': 'GET /admin/dashboard/stats',
                    'logs': 'GET /admin/logs'
                },
                'dashboard': {
                    'get_dashboard': 'GET /dashboard/'
                },
                'reporting': {
                    'hospital_report': 'GET /reporting/hospital/<id>',
                    'user_activity_report': 'GET /reporting/user-activity',
                    'appointment_analytics': 'GET /reporting/appointments/analytics',
                    'blood_bank_analytics': 'GET /reporting/blood-bank/analytics',
                    'emergency_analytics': 'GET /reporting/emergency/analytics',
                    'export_report': 'GET /reporting/export/<report_type>'
                },
                'audit': {
                    'log_action': 'POST /audit/log',
                    'get_logs': 'GET /audit/logs',
                    'get_user_logs': 'GET /audit/user/<id>/logs',
                    'security_events': 'GET /audit/security/events',
                    'login_attempts': 'GET /audit/security/login-attempts',
                    'export_logs': 'GET /audit/export'
                },
                'notifications': {
                    'send_notification': 'POST /notifications/send',
                    'get_notifications': 'GET /notifications/',
                    'mark_read': 'PUT /notifications/<id>/read',
                    'get_unread_count': 'GET /notifications/unread-count',
                    'bulk_mark_read': 'PUT /notifications/bulk-read',
                    'delete_notification': 'DELETE /notifications/<id>'
                }
            }
        }
    )


@main_bp.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Simple database connectivity check
        hospital_count = Hospital.query.count()
        return create_success_response(
            'Service is healthy',
            {
                'status': 'healthy',
                'database': 'connected',
                'hospitals_count': hospital_count
            }
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Service is unhealthy',
            'status': 'unhealthy',
            'error': str(e)
        }), 503
