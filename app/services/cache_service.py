import redis
import json
import pickle
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app
import logging
from typing import Any, Optional, Union, Dict
import hashlib


class CacheService:
    """Redis-based caching service for performance optimization"""
    
    def __init__(self):
        self.redis_client = None
        self.logger = logging.getLogger(__name__)
        self.default_ttl = 3600  # 1 hour
        self.key_prefix = "hospital_mgmt:"
    
    def init_app(self, app):
        """Initialize cache service with Flask app"""
        try:
            redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            self.logger.info("Redis cache service initialized successfully")
            
            # Set cache configuration
            self.default_ttl = app.config.get('CACHE_DEFAULT_TTL', 3600)
            self.key_prefix = app.config.get('CACHE_KEY_PREFIX', 'hospital_mgmt:')
            
        except Exception as e:
            self.logger.warning(f"Redis not available, caching disabled: {str(e)}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.redis_client is not None
    
    def _make_key(self, key: str) -> str:
        """Create a prefixed cache key"""
        return f"{self.key_prefix}{key}"
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a value in cache"""
        if not self.is_available():
            return False
        
        try:
            cache_key = self._make_key(key)
            ttl = ttl or self.default_ttl
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = pickle.dumps(value)
            
            self.redis_client.setex(cache_key, ttl, serialized_value)
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    def get(self, key: str) -> Any:
        """Get a value from cache"""
        if not self.is_available():
            return None
        
        try:
            cache_key = self._make_key(key)
            value = self.redis_client.get(cache_key)
            
            if value is None:
                return None
            
            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(value)
                
        except Exception as e:
            self.logger.error(f"Error getting cache key {key}: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache"""
        if not self.is_available():
            return False
        
        try:
            cache_key = self._make_key(key)
            self.redis_client.delete(cache_key)
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache"""
        if not self.is_available():
            return False
        
        try:
            cache_key = self._make_key(key)
            return bool(self.redis_client.exists(cache_key))
            
        except Exception as e:
            self.logger.error(f"Error checking cache key {key}: {str(e)}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration time for a key"""
        if not self.is_available():
            return False
        
        try:
            cache_key = self._make_key(key)
            self.redis_client.expire(cache_key, ttl)
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting expiration for cache key {key}: {str(e)}")
            return False
    
    def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern"""
        if not self.is_available():
            return 0
        
        try:
            cache_pattern = self._make_key(pattern)
            keys = self.redis_client.keys(cache_pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
            
        except Exception as e:
            self.logger.error(f"Error flushing cache pattern {pattern}: {str(e)}")
            return 0
    
    def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> Optional[int]:
        """Increment a numeric value"""
        if not self.is_available():
            return None
        
        try:
            cache_key = self._make_key(key)
            
            # Use pipeline for atomic operation
            pipe = self.redis_client.pipeline()
            pipe.incrby(cache_key, amount)
            
            if ttl and not self.redis_client.exists(cache_key):
                pipe.expire(cache_key, ttl)
            
            result = pipe.execute()
            return result[0]
            
        except Exception as e:
            self.logger.error(f"Error incrementing cache key {key}: {str(e)}")
            return None
    
    def set_hash(self, key: str, field: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set a field in a hash"""
        if not self.is_available():
            return False
        
        try:
            cache_key = self._make_key(key)
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)
            
            self.redis_client.hset(cache_key, field, serialized_value)
            
            if ttl:
                self.redis_client.expire(cache_key, ttl)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting hash field {key}:{field}: {str(e)}")
            return False
    
    def get_hash(self, key: str, field: str) -> Any:
        """Get a field from a hash"""
        if not self.is_available():
            return None
        
        try:
            cache_key = self._make_key(key)
            value = self.redis_client.hget(cache_key, field)
            
            if value is None:
                return None
            
            # Try to deserialize as JSON
            try:
                return json.loads(value.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return value.decode('utf-8')
                
        except Exception as e:
            self.logger.error(f"Error getting hash field {key}:{field}: {str(e)}")
            return None
    
    def get_hash_all(self, key: str) -> Optional[Dict[str, Any]]:
        """Get all fields from a hash"""
        if not self.is_available():
            return None
        
        try:
            cache_key = self._make_key(key)
            hash_data = self.redis_client.hgetall(cache_key)
            
            if not hash_data:
                return None
            
            result = {}
            for field, value in hash_data.items():
                field_name = field.decode('utf-8') if isinstance(field, bytes) else field
                
                # Try to deserialize as JSON
                try:
                    result[field_name] = json.loads(value.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    result[field_name] = value.decode('utf-8') if isinstance(value, bytes) else value
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting all hash fields {key}: {str(e)}")
            return None
    
    def add_to_set(self, key: str, *values, ttl: Optional[int] = None) -> bool:
        """Add values to a set"""
        if not self.is_available():
            return False
        
        try:
            cache_key = self._make_key(key)
            
            # Serialize values
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serialized_values.append(json.dumps(value, default=str))
                else:
                    serialized_values.append(str(value))
            
            self.redis_client.sadd(cache_key, *serialized_values)
            
            if ttl:
                self.redis_client.expire(cache_key, ttl)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding to set {key}: {str(e)}")
            return False
    
    def get_set_members(self, key: str) -> Optional[set]:
        """Get all members of a set"""
        if not self.is_available():
            return None
        
        try:
            cache_key = self._make_key(key)
            members = self.redis_client.smembers(cache_key)
            
            result = set()
            for member in members:
                # Try to deserialize as JSON
                try:
                    result.add(json.loads(member.decode('utf-8')))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    result.add(member.decode('utf-8') if isinstance(member, bytes) else member)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting set members {key}: {str(e)}")
            return None
    
    def is_set_member(self, key: str, value: Any) -> bool:
        """Check if a value is in a set"""
        if not self.is_available():
            return False
        
        try:
            cache_key = self._make_key(key)
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)
            
            return bool(self.redis_client.sismember(cache_key, serialized_value))
            
        except Exception as e:
            self.logger.error(f"Error checking set membership {key}: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.is_available():
            return {'available': False}
        
        try:
            info = self.redis_client.info()
            
            return {
                'available': True,
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'expired_keys': info.get('expired_keys', 0),
                'evicted_keys': info.get('evicted_keys', 0),
                'total_commands_processed': info.get('total_commands_processed', 0),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {str(e)}")
            return {'available': False, 'error': str(e)}


# Cache decorators for common patterns
def cached(ttl: int = 3600, key_pattern: str = None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not cache_service.is_available():
                return func(*args, **kwargs)
            
            # Generate cache key
            if key_pattern:
                cache_key = key_pattern.format(*args, **kwargs)
            else:
                # Generate key based on function name and arguments
                key_data = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
                cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Try to get from cache
            result = cache_service.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_invalidate(pattern: str):
    """Decorator to invalidate cache patterns after function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if cache_service.is_available():
                cache_service.flush_pattern(pattern)
            
            return result
        
        return wrapper
    return decorator


# Hospital-specific cache patterns
class HospitalCache:
    """Hospital-specific caching patterns"""
    
    @staticmethod
    def get_hospital_stats(hospital_id: int) -> Optional[Dict]:
        """Get cached hospital statistics"""
        key = f"hospital:{hospital_id}:stats"
        return cache_service.get(key)
    
    @staticmethod
    def set_hospital_stats(hospital_id: int, stats: Dict, ttl: int = 300) -> bool:
        """Cache hospital statistics (5 minutes default)"""
        key = f"hospital:{hospital_id}:stats"
        return cache_service.set(key, stats, ttl)
    
    @staticmethod
    def get_bed_availability(hospital_id: int) -> Optional[Dict]:
        """Get cached bed availability"""
        key = f"hospital:{hospital_id}:beds"
        return cache_service.get(key)
    
    @staticmethod
    def set_bed_availability(hospital_id: int, bed_data: Dict, ttl: int = 60) -> bool:
        """Cache bed availability (1 minute default)"""
        key = f"hospital:{hospital_id}:beds"
        return cache_service.set(key, bed_data, ttl)
    
    @staticmethod
    def invalidate_hospital_data(hospital_id: int):
        """Invalidate all cached data for a hospital"""
        cache_service.flush_pattern(f"hospital:{hospital_id}:*")


# Appointment-specific cache patterns
class AppointmentCache:
    """Appointment-specific caching patterns"""
    
    @staticmethod
    def get_available_slots(hospital_id: int, date: str) -> Optional[list]:
        """Get cached available appointment slots"""
        key = f"appointments:slots:{hospital_id}:{date}"
        return cache_service.get(key)
    
    @staticmethod
    def set_available_slots(hospital_id: int, date: str, slots: list, ttl: int = 300) -> bool:
        """Cache available appointment slots"""
        key = f"appointments:slots:{hospital_id}:{date}"
        return cache_service.set(key, slots, ttl)
    
    @staticmethod
    def invalidate_appointment_slots(hospital_id: int, date: str = None):
        """Invalidate appointment slots cache"""
        if date:
            cache_service.delete(f"appointments:slots:{hospital_id}:{date}")
        else:
            cache_service.flush_pattern(f"appointments:slots:{hospital_id}:*")


# Blood bank cache patterns
class BloodBankCache:
    """Blood bank caching patterns"""
    
    @staticmethod
    def get_blood_inventory(bloodbank_id: int) -> Optional[Dict]:
        """Get cached blood inventory"""
        key = f"bloodbank:{bloodbank_id}:inventory"
        return cache_service.get(key)
    
    @staticmethod
    def set_blood_inventory(bloodbank_id: int, inventory: Dict, ttl: int = 180) -> bool:
        """Cache blood inventory (3 minutes default)"""
        key = f"bloodbank:{bloodbank_id}:inventory"
        return cache_service.set(key, inventory, ttl)
    
    @staticmethod
    def invalidate_blood_inventory(bloodbank_id: int):
        """Invalidate blood inventory cache"""
        cache_service.delete(f"bloodbank:{bloodbank_id}:inventory")


# Session and rate limiting cache patterns
class SessionCache:
    """Session and rate limiting cache patterns"""
    
    @staticmethod
    def track_login_attempt(ip_address: str, username: str = None) -> int:
        """Track login attempts for rate limiting"""
        key = f"login_attempts:{ip_address}"
        if username:
            key += f":{username}"
        
        return cache_service.increment(key, ttl=900) or 0  # 15 minutes
    
    @staticmethod
    def is_ip_blocked(ip_address: str) -> bool:
        """Check if IP is temporarily blocked"""
        key = f"blocked_ip:{ip_address}"
        return cache_service.exists(key)
    
    @staticmethod
    def block_ip(ip_address: str, ttl: int = 3600) -> bool:
        """Temporarily block an IP address"""
        key = f"blocked_ip:{ip_address}"
        return cache_service.set(key, "blocked", ttl)
    
    @staticmethod
    def store_session_data(session_id: str, data: Dict, ttl: int = 3600) -> bool:
        """Store session data"""
        key = f"session:{session_id}"
        return cache_service.set(key, data, ttl)
    
    @staticmethod
    def get_session_data(session_id: str) -> Optional[Dict]:
        """Get session data"""
        key = f"session:{session_id}"
        return cache_service.get(key)


# Global cache service instance
cache_service = CacheService()


def init_cache_service(app):
    """Initialize cache service with Flask app"""
    cache_service.init_app(app)
    return cache_service
