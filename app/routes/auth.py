from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import timedelta
from app.models import db, Users, Admin, Hospital_info
from app.utils.helpers import (
    hash_password, check_password, validate_email,
    validate_password_strength, create_success_response,
    create_error_response, serialize_model
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset (placeholder implementation)"""
    try:
        data = request.get_json()
        
        if not data.get('email'):
            return create_error_response('email is required', status_code=400)
        
        # Check if user exists
        user = Users.query.filter_by(email=data['email']).first()
        if not user:
            # Don't reveal if email exists for security reasons
            return create_success_response(
                'If the email exists, a password reset link will be sent',
                {}
            )
        
        # In a real implementation, you would:
        # 1. Generate a secure reset token
        # 2. Store it in database with expiry
        # 3. Send email with reset link
        
        return create_success_response(
            'Password reset instructions sent to email if account exists',
            {}
        )
        
    except Exception as e:
        return create_error_response(f'Password reset request failed: {str(e)}', status_code=500)


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'fullname', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', status_code=400)
        
        # Validate email format
        if not validate_email(data['email']):
            return create_error_response('Invalid email format', status_code=400)
        
        # Validate password strength
        is_strong, message = validate_password_strength(data['password'])
        if not is_strong:
            return create_error_response(message, status_code=400)
        
        # Check if user already exists
        if Users.query.filter_by(username=data['username']).first():
            return create_error_response('Username already exists', status_code=409)
        
        if Users.query.filter_by(email=data['email']).first():
            return create_error_response('Email already registered', status_code=409)
        
        # Hash password
        hashed_password = hash_password(data['password'])
        
        # Create new user
        user = Users(
            username=data['username'],
            fullname=data['fullname'],
            email=data['email'],
            password=hashed_password,
            phone_num=data.get('phone_num'),
            location=data.get('location'),
            role=data.get('role', 'user')  # Default role is 'user'
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create tokens
        additional_claims = {
            'role': user.role,
            'type': 'user'
        }
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(identity=user.id)
        
        user_data = serialize_model(user, exclude=['password'])
        
        return create_success_response(
            'User registered successfully',
            {
                'user': user_data,
                'access_token': access_token,
                'refresh_token': refresh_token
            },
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Registration failed: {str(e)}', status_code=500)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return create_error_response('Username and password are required', status_code=400)
        
        # Check user credentials
        user = Users.query.filter_by(username=data['username']).first()
        
        if not user or not check_password(data['password'], user.password):
            return create_error_response('Invalid credentials', status_code=401)
        
        # Create tokens
        additional_claims = {
            'role': user.role,
            'type': 'user'
        }
        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(identity=user.id)
        
        user_data = serialize_model(user, exclude=['password'])
        
        return create_success_response(
            'Login successful',
            {
                'user': user_data,
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        )
        
    except Exception as e:
        return create_error_response(f'Login failed: {str(e)}', status_code=500)


@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login"""
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return create_error_response('Username and password are required', status_code=400)
        
        # Check admin credentials
        admin = Admin.query.filter_by(username=data['username']).first()
        
        if not admin or not check_password(data['password'], admin.password):
            return create_error_response('Invalid admin credentials', status_code=401)
        
        # Create tokens
        additional_claims = {
            'role': 'admin',
            'type': 'admin'
        }
        access_token = create_access_token(
            identity=admin.id,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(identity=admin.id)
        
        admin_data = serialize_model(admin, exclude=['password'])
        
        return create_success_response(
            'Admin login successful',
            {
                'admin': admin_data,
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        )
        
    except Exception as e:
        return create_error_response(f'Admin login failed: {str(e)}', status_code=500)


@auth_bp.route('/hospital/login', methods=['POST'])
def hospital_login():
    """Hospital login"""
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return create_error_response('Username and password are required', status_code=400)
        
        # Check hospital credentials
        hospital_info = Hospital_info.query.filter_by(username=data['username']).first()
        
        if not hospital_info or not check_password(data['password'], hospital_info.password):
            return create_error_response('Invalid hospital credentials', status_code=401)
        
        # Create tokens
        additional_claims = {
            'role': 'hospital_admin',
            'type': 'hospital'
        }
        access_token = create_access_token(
            identity=hospital_info.id,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(identity=hospital_info.id)
        
        hospital_data = serialize_model(hospital_info, exclude=['password'])
        
        return create_success_response(
            'Hospital login successful',
            {
                'hospital': hospital_data,
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        )
        
    except Exception as e:
        return create_error_response(f'Hospital login failed: {str(e)}', status_code=500)


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        
        # Create new access token with same claims
        additional_claims = {
            'role': claims.get('role'),
            'type': claims.get('type', 'user')
        }
        new_access_token = create_access_token(
            identity=current_user_id,
            additional_claims=additional_claims
        )
        
        return create_success_response(
            'Token refreshed successfully',
            {'access_token': new_access_token}
        )
        
    except Exception as e:
        return create_error_response(f'Token refresh failed: {str(e)}', status_code=500)


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (in a real application, you would blacklist the token)"""
    try:
        # In a production application, you would add the token to a blacklist
        # For now, we'll just return a success message
        return create_success_response('Logout successful')
        
    except Exception as e:
        return create_error_response(f'Logout failed: {str(e)}', status_code=500)


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_type = claims.get('type', 'user')
        
        if user_type == 'admin':
            user = Admin.query.get(current_user_id)
        elif user_type == 'hospital':
            user = Hospital_info.query.get(current_user_id)
        else:
            user = Users.query.get(current_user_id)
        
        if not user:
            return create_error_response('User not found', status_code=404)
        
        user_data = serialize_model(user, exclude=['password'])
        
        return create_success_response(
            'Profile retrieved successfully',
            {'user': user_data}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to get profile: {str(e)}', status_code=500)


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_type = claims.get('type', 'user')
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return create_error_response('Current password and new password are required', status_code=400)
        
        # Get user based on type
        if user_type == 'admin':
            user = Admin.query.get(current_user_id)
        elif user_type == 'hospital':
            user = Hospital_info.query.get(current_user_id)
        else:
            user = Users.query.get(current_user_id)
        
        if not user:
            return create_error_response('User not found', status_code=404)
        
        # Verify current password
        if not check_password(data['current_password'], user.password):
            return create_error_response('Current password is incorrect', status_code=400)
        
        # Validate new password strength
        is_strong, message = validate_password_strength(data['new_password'])
        if not is_strong:
            return create_error_response(message, status_code=400)
        
        # Hash and save new password
        user.password = hash_password(data['new_password'])
        db.session.commit()
        
        return create_success_response('Password changed successfully')
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Password change failed: {str(e)}', status_code=500)


'''
Routes left for testing :
-------------------------
1. forgot-Password
2. refresh
3. change-password
'''