from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import db, Users
from app.auth.decorators import admin_required, get_current_user
from app.utils.helpers import (
    validate_email, validate_phone, serialize_model,
    create_success_response, create_error_response, paginate_query,
    hash_password, check_password, validate_password_strength
)

user_bp = Blueprint('user', __name__)


@user_bp.route('/profile/update', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_type = claims.get('type', 'user')
        
        # Only regular users can update profile through this endpoint
        if user_type != 'user':
            return create_error_response('This endpoint is for regular users only', status_code=403)
        
        user = Users.query.get(current_user_id)
        if not user:
            return create_error_response('User not found', status_code=404)
        
        data = request.get_json()
        
        # Update allowed fields
        if 'fullname' in data:
            user.fullname = data['fullname']
        
        if 'email' in data:
            if not validate_email(data['email']):
                return create_error_response('Invalid email format', status_code=400)
            
            # Check if email is already taken by another user
            existing_user = Users.query.filter(
                Users.email == data['email'],
                Users.id != current_user_id
            ).first()
            if existing_user:
                return create_error_response('Email already registered', status_code=409)
            
            user.email = data['email']
        
        if 'phone_num' in data:
            if data['phone_num'] and not validate_phone(data['phone_num']):
                return create_error_response('Invalid phone number format', status_code=400)
            user.phone_num = data['phone_num']
        
        if 'location' in data:
            user.location = data['location']
        
        db.session.commit()
        
        user_data = serialize_model(user, exclude=['password'])
        
        return create_success_response(
            'Profile updated successfully',
            {'user': user_data}
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Profile update failed: {str(e)}', status_code=500)


@user_bp.route('/all', methods=['GET'])
@admin_required
def get_all_users():
    """Get all users (admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        role_filter = request.args.get('role')
        search = request.args.get('search')
        
        query = Users.query
        
        # Apply filters
        if role_filter:
            query = query.filter(Users.role == role_filter)
        
        if search:
            query = query.filter(
                Users.fullname.ilike(f'%{search}%') |
                Users.username.ilike(f'%{search}%') |
                Users.email.ilike(f'%{search}%')
            )
        
        # Order by creation date (newest first)
        query = query.order_by(Users.created_at.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        users = []
        for user in pagination.items:
            users.append(serialize_model(user, exclude=['password']))
        
        return create_success_response(
            'Users retrieved successfully',
            {
                'users': users,
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
        return create_error_response(f'Failed to retrieve users: {str(e)}', status_code=500)


@user_bp.route('/delete/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        
        # Prevent admin from deleting themselves
        if user_id == current_user_id:
            return create_error_response('Cannot delete your own account', status_code=400)
        
        user = Users.query.get(user_id)
        if not user:
            return create_error_response('User not found', status_code=404)
        
        # Store user info for logging
        deleted_user_info = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        }
        
        db.session.delete(user)
        db.session.commit()
        
        return create_success_response(
            'User deleted successfully',
            {'deleted_user': deleted_user_info}
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'User deletion failed: {str(e)}', status_code=500)


@user_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Get user details"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role')
        
        # Users can only view their own profile unless they're admin
        if user_id != current_user_id and user_role != 'admin':
            return create_error_response('Access denied', status_code=403)
        
        user = Users.query.get(user_id)
        if not user:
            return create_error_response('User not found', status_code=404)
        
        user_data = serialize_model(user, exclude=['password'])
        
        return create_success_response(
            'User details retrieved successfully',
            {'user': user_data}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve user: {str(e)}', status_code=500)


@user_bp.route('/update-role/<int:user_id>', methods=['PUT'])
@admin_required
def update_user_role(user_id):
    """Update user role (admin only)"""
    try:
        user = Users.query.get(user_id)
        if not user:
            return create_error_response('User not found', status_code=404)
        
        data = request.get_json()
        new_role = data.get('role')
        
        if not new_role:
            return create_error_response('Role is required', status_code=400)
        
        # Validate role
        allowed_roles = ['user', 'doctor', 'hospital_admin', 'donor', 'ambulance_driver']
        if new_role not in allowed_roles:
            return create_error_response(
                f'Invalid role. Allowed roles: {", ".join(allowed_roles)}',
                status_code=400
            )
        
        old_role = user.role
        user.role = new_role
        db.session.commit()
        
        user_data = serialize_model(user, exclude=['password'])
        
        return create_success_response(
            f'User role updated from {old_role} to {new_role}',
            {'user': user_data}
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Role update failed: {str(e)}', status_code=500)


@user_bp.route('/stats', methods=['GET'])
@admin_required
def get_user_stats():
    """Get user statistics (admin only)"""
    try:
        total_users = Users.query.count()
        
        # Count by role
        role_stats = {}
        for role in ['user', 'doctor', 'hospital_admin', 'donor', 'ambulance_driver']:
            count = Users.query.filter(Users.role == role).count()
            role_stats[role] = count
        
        # Recent registrations (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_registrations = Users.query.filter(
            Users.created_at >= thirty_days_ago
        ).count()
        
        stats = {
            'total_users': total_users,
            'role_distribution': role_stats,
            'recent_registrations': recent_registrations
        }
        
        return create_success_response(
            'User statistics retrieved successfully',
            {'stats': stats}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve stats: {str(e)}', status_code=500)


@user_bp.route('/search', methods=['GET'])
@jwt_required()
def search_users():
    """Search users"""
    try:
        claims = get_jwt()
        user_role = claims.get('role')
        
        # Only admin and hospital_admin can search all users
        if user_role not in ['admin', 'hospital_admin']:
            return create_error_response('Access denied', status_code=403)
        
        search_term = request.args.get('q')
        if not search_term:
            return create_error_response('Search term is required', status_code=400)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Search in multiple fields
        query = Users.query.filter(
            Users.fullname.ilike(f'%{search_term}%') |
            Users.username.ilike(f'%{search_term}%') |
            Users.email.ilike(f'%{search_term}%')
        ).order_by(Users.fullname)
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        users = []
        for user in pagination.items:
            users.append(serialize_model(user, exclude=['password']))
        
        return create_success_response(
            f'Found {pagination.total} users matching "{search_term}"',
            {
                'users': users,
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
        return create_error_response(f'Search failed: {str(e)}', status_code=500)


'''
Routes left for testing :
------------------------

1. /profile/update
2. /<int:user_id>
3. /delete/<int:user_id>
4. /update-role/<int:user_id>
'''