from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Admin, Users, Hospital, AdminLog
from app.auth.decorators import admin_required
from app.utils.helpers import (
    hash_password, serialize_model, create_success_response, create_error_response
)

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/create', methods=['POST'])
@admin_required
def create_admin():
    """Create a new admin user"""
    try:
        data = request.get_json()
        
        required_fields = ['username', 'password']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', status_code=400)
        
        if Admin.query.filter_by(username=data['username']).first():
            return create_error_response('Username already exists', status_code=409)
        
        admin = Admin(
            username=data['username'],
            password=hash_password(data['password']),
            role=data.get('role', 'admin')
        )
        
        db.session.add(admin)
        db.session.commit()
        
        # Converts the admin object to a JSON-serializable format.
        # It excludes the password from the response for security.
        admin_data = serialize_model(admin, exclude=['password'])
        
        return create_success_response(
            'Admin created successfully',
            {'admin': admin_data},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Admin creation failed: {str(e)}', status_code=500)

@admin_bp.route('/dashboard/stats', methods=['GET'])
@admin_required
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = {
            'total_users': Users.query.count(),
            'total_hospitals': Hospital.query.count(),
            'total_admins': Admin.query.count()
        }
        
        return create_success_response(
            'Dashboard statistics retrieved successfully',
            {'stats': stats}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve stats: {str(e)}', status_code=500)

@admin_bp.route('/logs', methods=['GET'])
@admin_required
def get_admin_logs():
    """Get admin activity logs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        query = AdminLog.query.order_by(AdminLog.timestamp.desc())
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        logs = []
        for log in pagination.items:
            log_data = serialize_model(log)
            if log.admin:
                log_data['admin'] = serialize_model(log.admin, exclude=['password'])
            if log.user:
                log_data['user'] = serialize_model(log.user, exclude=['password'])
            logs.append(log_data)
        
        return create_success_response(
            'Admin logs retrieved successfully',
            {
                'logs': logs,
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
        return create_error_response(f'Failed to retrieve logs: {str(e)}', status_code=500)
