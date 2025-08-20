import bcrypt
import re
import secrets
import string
from datetime import datetime
from flask import current_app
import os
from werkzeug.utils import secure_filename


def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def check_password(password, hashed_password):
    """Check if a password matches its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def validate_email(email):
    """Validate email format"""
    email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return email_regex.match(email) is not None


def validate_phone(phone):
    """Validate phone number format"""
    phone_regex = re.compile(r'^\+?1?\d{9,15}$')
    return phone_regex.match(phone.replace(' ', '').replace('-', '')) is not None


def validate_password_strength(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is strong"


def generate_random_string(length=32):
    """Generate a random string"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_otp(length=6):
    """Generate a random OTP"""
    digits = string.digits
    return ''.join(secrets.choice(digits) for _ in range(length))


def allowed_file(filename, allowed_extensions):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def save_uploaded_file(file, upload_folder, allowed_extensions=None):
    """Save an uploaded file securely"""
    if not allowed_extensions:
        allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    
    if file and allowed_file(file.filename, allowed_extensions):
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = generate_random_string(8)
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{name}_{timestamp}_{random_suffix}{ext}"
        
        # Ensure upload folder exists
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        return unique_filename
    
    return None


def format_datetime(dt):
    """Format datetime for JSON serialization"""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return None


def format_date(date):
    """Format date for JSON serialization"""
    if date:
        return date.strftime('%Y-%m-%d')
    return None


def format_time(time):
    """Format time for JSON serialization"""
    if time:
        return time.strftime('%H:%M:%S')
    return None


def paginate_query(query, page, per_page, error_out=False):
    """Paginate a SQLAlchemy query"""
    return query.paginate(
        page=page,
        per_page=per_page,
        error_out=error_out
    )


def serialize_model(model, fields=None, exclude=None):
    """Serialize a SQLAlchemy model to dictionary"""
    data = {}
    
    for column in model.__table__.columns:
        if exclude and column.name in exclude:
            continue
        if fields and column.name not in fields:
            continue
            
        value = getattr(model, column.name)
        
        # Handle different data types
        if isinstance(value, datetime):
            data[column.name] = format_datetime(value)
        elif hasattr(value, 'date') and callable(getattr(value, 'date')):
            data[column.name] = format_date(value)
        elif hasattr(value, 'strftime') and not isinstance(value, datetime):  # Time objects
            data[column.name] = format_time(value)
        elif hasattr(value, 'value'):  # Enum values
            data[column.name] = value.value
        else:
            data[column.name] = value
    
    return data


def validate_required_fields(data, required_fields):
    """Validate required fields in request data"""
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, "All required fields present"


def sanitize_string(text, max_length=None):
    """Sanitize string input"""
    if not text:
        return ""
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Limit length if specified
    if max_length:
        text = text[:max_length]
    
    return text


def generate_hospital_registration_id():
    """Generate a unique hospital registration ID"""
    timestamp = datetime.now().strftime('%Y%m%d')
    random_part = generate_random_string(6).upper()
    return f"HOSP{timestamp}{random_part}"


def generate_appointment_id():
    """Generate a unique appointment ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = generate_random_string(4).upper()
    return f"APT{timestamp}{random_part}"


def generate_opd_slot_id():
    """Generate a unique OPD slot ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_part = generate_random_string(4).upper()
    return f"OPD{timestamp}{random_part}"


def calculate_age(birth_date):
    """Calculate age from birth date"""
    if not birth_date:
        return None
    
    today = datetime.now().date()
    if isinstance(birth_date, datetime):
        birth_date = birth_date.date()
    
    age = today.year - birth_date.year
    if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return age


def create_success_response(message, data=None, status_code=200):
    """Create a standardized success response"""
    response = {
        'success': True,
        'message': message
    }
    if data is not None:
        response['data'] = data
    
    return response, status_code


def create_error_response(message, errors=None, status_code=400):
    """Create a standardized error response"""
    response = {
        'success': False,
        'message': message
    }
    if errors:
        response['errors'] = errors
    
    return response, status_code
