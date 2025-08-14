from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from app.models import Users, Admin, Hospital_info


def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Token is invalid', 'error': str(e)}), 401
    return decorated


def role_required(*allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                verify_jwt_in_request()
                current_user_id = get_jwt_identity()
                
                # Get additional claims from token
                claims = get_jwt()
                user_role = claims.get('role')
                
                if user_role not in allowed_roles:
                    return jsonify({'message': 'Access denied. Insufficient permissions'}), 403
                
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'message': 'Access denied', 'error': str(e)}), 401
        return decorated
    return decorator


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            claims = get_jwt()
            user_role = claims.get('role')
            
            # Check if we have a valid admin role and identity
            if user_role != 'admin':
                return jsonify({'message': 'Admin access required'}), 403
            
            # Ensure identity is valid (can be string or int)
            if current_user_id is None:
                return jsonify({'message': 'Invalid token identity'}), 401
            
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Admin access required', 'error': str(e)}), 401
    return decorated


def hospital_admin_or_admin_required(f):
    """Decorator to require hospital admin or system admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role')
            
            if user_role not in ['admin', 'hospital_admin']:
                return jsonify({'message': 'Hospital admin or system admin access required'}), 403
            
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Access denied', 'error': str(e)}), 401
    return decorated


def doctor_or_admin_required(f):
    """Decorator to require doctor or admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role')
            
            if user_role not in ['doctor', 'admin', 'hospital_admin']:
                return jsonify({'message': 'Doctor or admin access required'}), 403
            
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Access denied', 'error': str(e)}), 401
    return decorated


def get_current_user():
    """Get current authenticated user"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_type = claims.get('type', 'user')
        
        if user_type == 'admin':
            return Admin.query.get(current_user_id)
        elif user_type == 'hospital':
            return Hospital_info.query.get(current_user_id)
        else:
            return Users.query.get(current_user_id)
    except:
        return None


def api_key_required(f):
    """Decorator for API key authentication (for external services)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'message': 'API key required'}), 401
        
        # In a real application, validate the API key against a database
        # For now, we'll use a simple check
        valid_api_keys = ['emergency-service-key', 'ambulance-service-key']
        
        if api_key not in valid_api_keys:
            return jsonify({'message': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated
