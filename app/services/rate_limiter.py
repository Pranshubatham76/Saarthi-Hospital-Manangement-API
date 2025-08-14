from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g, current_app
from flask_jwt_extended import get_jwt_identity, get_jwt
import time
import logging
from typing import Optional, Dict, Tuple
from app.services.cache_service import cache_service
from app.utils.helpers import create_error_response


class RateLimiter:
    """Advanced rate limiting service with multiple strategies"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.default_limits = {
            'auth': {'requests': 5, 'window': 300},      # 5 requests per 5 minutes for auth endpoints
            'api': {'requests': 100, 'window': 60},       # 100 requests per minute for regular API
            'upload': {'requests': 10, 'window': 300},    # 10 uploads per 5 minutes
            'emergency': {'requests': 3, 'window': 60},   # 3 emergency calls per minute
            'admin': {'requests': 200, 'window': 60},     # 200 requests per minute for admins
        }
        self.user_role_multipliers = {
            'admin': 3.0,
            'hospital_admin': 2.0,
            'doctor': 2.0,
            'user': 1.0,
            'guest': 0.5
        }
    
    def _get_client_identifier(self) -> str:
        """Get unique identifier for the client"""
        # Try to get user ID first
        try:
            user_id = get_jwt_identity()
            if user_id:
                claims = get_jwt()
                user_type = claims.get('type', 'user')
                return f"user:{user_type}:{user_id}"
        except:
            pass
        
        # Fall back to IP address
        ip = self._get_client_ip()
        return f"ip:{ip}"
    
    def _get_client_ip(self) -> str:
        """Get client IP address considering proxies"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'
    
    def _get_rate_limit_key(self, identifier: str, limit_type: str) -> str:
        """Generate cache key for rate limiting"""
        window_start = int(time.time() / self.default_limits[limit_type]['window'])
        return f"rate_limit:{limit_type}:{identifier}:{window_start}"
    
    def _get_user_role_multiplier(self) -> float:
        """Get rate limit multiplier based on user role"""
        try:
            claims = get_jwt()
            user_role = claims.get('role', 'user')
            return self.user_role_multipliers.get(user_role, 1.0)
        except:
            return 0.5  # Guest users get reduced limits
    
    def check_rate_limit(self, limit_type: str = 'api', custom_limit: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """
        Check if request is within rate limits
        Returns (is_allowed, limit_info)
        """
        if not cache_service.is_available():
            # If cache is not available, allow request but log warning
            self.logger.warning("Rate limiting disabled - cache service unavailable")
            return True, {}
        
        try:
            identifier = self._get_client_identifier()
            
            # Get limit configuration
            if custom_limit:
                limit_config = custom_limit
            else:
                limit_config = self.default_limits.get(limit_type, self.default_limits['api'])
            
            # Apply user role multiplier
            multiplier = self._get_user_role_multiplier()
            adjusted_limit = int(limit_config['requests'] * multiplier)
            window = limit_config['window']
            
            # Generate cache key
            key = self._get_rate_limit_key(identifier, limit_type)
            
            # Get current count
            current_count = cache_service.increment(key, ttl=window)
            
            # Check if limit exceeded
            is_allowed = current_count <= adjusted_limit
            
            # Calculate reset time
            window_start = int(time.time() / window) * window
            reset_time = window_start + window
            
            limit_info = {
                'limit': adjusted_limit,
                'remaining': max(0, adjusted_limit - current_count),
                'reset_time': reset_time,
                'retry_after': reset_time - int(time.time()) if not is_allowed else 0,
                'window': window,
                'identifier': identifier.split(':')[0]  # Only return type, not full identifier
            }
            
            return is_allowed, limit_info
            
        except Exception as e:
            self.logger.error(f"Error checking rate limit: {str(e)}")
            return True, {}  # Allow request on error
    
    def is_ip_blocked(self, ip_address: str = None) -> bool:
        """Check if IP address is temporarily blocked"""
        if not cache_service.is_available():
            return False
        
        ip = ip_address or self._get_client_ip()
        return cache_service.exists(f"blocked_ip:{ip}")
    
    def block_ip(self, ip_address: str, duration: int = 3600, reason: str = "Rate limit exceeded") -> bool:
        """Temporarily block an IP address"""
        if not cache_service.is_available():
            return False
        
        try:
            key = f"blocked_ip:{ip_address}"
            block_info = {
                'blocked_at': datetime.utcnow().isoformat(),
                'reason': reason,
                'duration': duration
            }
            
            cache_service.set(key, block_info, duration)
            self.logger.warning(f"IP {ip_address} blocked for {duration} seconds: {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error blocking IP {ip_address}: {str(e)}")
            return False
    
    def check_brute_force_protection(self, identifier: str, max_attempts: int = 5, 
                                   window: int = 900) -> Tuple[bool, int]:
        """
        Check for brute force attempts
        Returns (is_blocked, attempts_count)
        """
        if not cache_service.is_available():
            return False, 0
        
        try:
            key = f"brute_force:{identifier}"
            attempts = cache_service.increment(key, ttl=window) or 0
            
            if attempts > max_attempts:
                # Block the identifier
                self.block_ip(identifier.split(':')[-1] if ':' in identifier else identifier, 
                             window, "Brute force protection")
                return True, attempts
            
            return False, attempts
            
        except Exception as e:
            self.logger.error(f"Error checking brute force protection: {str(e)}")
            return False, 0
    
    def track_failed_login(self, username: str, ip_address: str = None) -> bool:
        """Track failed login attempts for brute force protection"""
        if not cache_service.is_available():
            return False
        
        ip = ip_address or self._get_client_ip()
        
        # Track by IP
        is_ip_blocked, ip_attempts = self.check_brute_force_protection(ip, max_attempts=10, window=900)
        
        # Track by username
        is_user_blocked, user_attempts = self.check_brute_force_protection(
            f"user:{username}", max_attempts=5, window=1800
        )
        
        # Track by IP+username combination
        is_combo_blocked, combo_attempts = self.check_brute_force_protection(
            f"combo:{ip}:{username}", max_attempts=3, window=600
        )
        
        if is_ip_blocked or is_user_blocked or is_combo_blocked:
            self.logger.warning(f"Brute force protection triggered for {username} from {ip}")
            return True
        
        return False
    
    def get_rate_limit_stats(self, identifier: str = None) -> Dict:
        """Get rate limiting statistics"""
        if not cache_service.is_available():
            return {'available': False}
        
        try:
            if not identifier:
                identifier = self._get_client_identifier()
            
            stats = {}
            
            for limit_type in self.default_limits.keys():
                key = self._get_rate_limit_key(identifier, limit_type)
                current_count = cache_service.get(key) or 0
                
                limit_config = self.default_limits[limit_type]
                multiplier = self._get_user_role_multiplier()
                adjusted_limit = int(limit_config['requests'] * multiplier)
                
                stats[limit_type] = {
                    'current_count': current_count,
                    'limit': adjusted_limit,
                    'remaining': max(0, adjusted_limit - current_count),
                    'window': limit_config['window']
                }
            
            return {
                'available': True,
                'identifier': identifier.split(':')[0],
                'limits': stats
            }
            
        except Exception as e:
            self.logger.error(f"Error getting rate limit stats: {str(e)}")
            return {'available': False, 'error': str(e)}
    
    def reset_rate_limits(self, identifier: str = None) -> bool:
        """Reset rate limits for an identifier (admin function)"""
        if not cache_service.is_available():
            return False
        
        try:
            if not identifier:
                identifier = self._get_client_identifier()
            
            # Reset all limit types for the identifier
            for limit_type in self.default_limits.keys():
                pattern = f"rate_limit:{limit_type}:{identifier}:*"
                cache_service.flush_pattern(pattern)
            
            # Also unblock if blocked
            if ':' in identifier:
                ip = identifier.split(':')[-1]
                cache_service.delete(f"blocked_ip:{ip}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting rate limits: {str(e)}")
            return False


# Global rate limiter instance
rate_limiter = RateLimiter()


# Decorators for easy rate limiting
def rate_limit(limit_type: str = 'api', custom_limit: Optional[Dict] = None):
    """Decorator to apply rate limiting to endpoints"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if IP is blocked
            if rate_limiter.is_ip_blocked():
                return create_error_response(
                    'Your IP address has been temporarily blocked due to suspicious activity',
                    status_code=429
                )
            
            # Check rate limits
            is_allowed, limit_info = rate_limiter.check_rate_limit(limit_type, custom_limit)
            
            if not is_allowed:
                response_data = create_error_response(
                    'Rate limit exceeded. Please try again later.',
                    status_code=429
                )
                
                # Add rate limit headers
                response = jsonify(response_data[0])
                response.status_code = response_data[1]
                response.headers['X-RateLimit-Limit'] = str(limit_info.get('limit', 0))
                response.headers['X-RateLimit-Remaining'] = str(limit_info.get('remaining', 0))
                response.headers['X-RateLimit-Reset'] = str(limit_info.get('reset_time', 0))
                response.headers['Retry-After'] = str(limit_info.get('retry_after', 60))
                
                return response
            
            # Store rate limit info in g for potential use in response headers
            g.rate_limit_info = limit_info
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def auth_rate_limit(func):
    """Specific rate limiter for authentication endpoints"""
    return rate_limit('auth')(func)


def emergency_rate_limit(func):
    """Specific rate limiter for emergency endpoints"""
    return rate_limit('emergency')(func)


def upload_rate_limit(func):
    """Specific rate limiter for file upload endpoints"""
    return rate_limit('upload')(func)


def admin_rate_limit(func):
    """Specific rate limiter for admin endpoints"""
    return rate_limit('admin')(func)


def brute_force_protection(max_attempts: int = 5, window: int = 900):
    """Decorator to protect against brute force attacks"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            identifier = rate_limiter._get_client_identifier()
            
            is_blocked, attempts = rate_limiter.check_brute_force_protection(
                identifier, max_attempts, window
            )
            
            if is_blocked:
                return create_error_response(
                    'Too many failed attempts. Your access has been temporarily blocked.',
                    status_code=429
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Middleware to add rate limit headers to responses
def add_rate_limit_headers(response):
    """Add rate limit headers to response"""
    if hasattr(g, 'rate_limit_info') and g.rate_limit_info:
        limit_info = g.rate_limit_info
        response.headers['X-RateLimit-Limit'] = str(limit_info.get('limit', 0))
        response.headers['X-RateLimit-Remaining'] = str(limit_info.get('remaining', 0))
        response.headers['X-RateLimit-Reset'] = str(limit_info.get('reset_time', 0))
    
    return response


# Context manager for temporary rate limit adjustments
class TemporaryRateLimit:
    """Context manager for temporarily adjusting rate limits"""
    
    def __init__(self, identifier: str, limit_type: str, multiplier: float, duration: int = 3600):
        self.identifier = identifier
        self.limit_type = limit_type
        self.multiplier = multiplier
        self.duration = duration
        self.original_key = None
    
    def __enter__(self):
        if not cache_service.is_available():
            return self
        
        # Store original limit
        key = f"temp_limit:{self.limit_type}:{self.identifier}"
        cache_service.set(key, {'multiplier': self.multiplier}, self.duration)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not cache_service.is_available():
            return
        
        # Remove temporary limit
        key = f"temp_limit:{self.limit_type}:{self.identifier}"
        cache_service.delete(key)


# Rate limit configuration manager
class RateLimitConfig:
    """Manage rate limit configurations"""
    
    @staticmethod
    def set_custom_limit(endpoint: str, requests: int, window: int, duration: int = 3600):
        """Set custom rate limit for specific endpoint"""
        if not cache_service.is_available():
            return False
        
        key = f"custom_limit:{endpoint}"
        limit_config = {'requests': requests, 'window': window}
        return cache_service.set(key, limit_config, duration)
    
    @staticmethod
    def get_custom_limit(endpoint: str) -> Optional[Dict]:
        """Get custom rate limit for endpoint"""
        if not cache_service.is_available():
            return None
        
        key = f"custom_limit:{endpoint}"
        return cache_service.get(key)
    
    @staticmethod
    def set_user_multiplier(user_id: int, multiplier: float, duration: int = 3600):
        """Set custom rate limit multiplier for specific user"""
        if not cache_service.is_available():
            return False
        
        key = f"user_multiplier:{user_id}"
        return cache_service.set(key, {'multiplier': multiplier}, duration)
    
    @staticmethod
    def get_user_multiplier(user_id: int) -> Optional[float]:
        """Get custom rate limit multiplier for user"""
        if not cache_service.is_available():
            return None
        
        key = f"user_multiplier:{user_id}"
        data = cache_service.get(key)
        return data.get('multiplier') if data else None


def init_rate_limiter(app):
    """Initialize rate limiter with Flask app"""
    # Add rate limit headers to all responses
    @app.after_request
    def after_request(response):
        return add_rate_limit_headers(response)
    
    return rate_limiter
