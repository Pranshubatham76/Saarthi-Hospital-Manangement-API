from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import db, Users, Hospital, Appointment, Emergency
from app.utils.helpers import serialize_model, create_success_response, create_error_response

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get dashboard data based on user role"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role')
        user_type = claims.get('type', 'user')
        
        if user_role == 'admin':
            return get_admin_dashboard()
        elif user_role == 'hospital_admin':
            return get_hospital_dashboard(current_user_id)
        elif user_role == 'doctor':
            return get_doctor_dashboard(current_user_id)
        else:
            return get_user_dashboard(current_user_id)
        
    except Exception as e:
        return create_error_response(f'Dashboard error: {str(e)}', status_code=500)


def get_admin_dashboard():
    """Get admin dashboard data"""
    try:
        stats = {
            'total_users': Users.query.count(),
            'total_hospitals': Hospital.query.count(),
            'total_appointments': Appointment.query.count(),
            'total_emergencies': Emergency.query.count()
        }
        
        # Recent activities
        recent_users = Users.query.order_by(Users.created_at.desc()).limit(5).all()
        recent_appointments = Appointment.query.order_by(Appointment.created_at.desc()).limit(5).all()
        recent_emergencies = Emergency.query.order_by(Emergency.created_at.desc()).limit(5).all()
        
        dashboard_data = {
            'stats': stats,
            'recent_users': [serialize_model(u, exclude=['password']) for u in recent_users],
            'recent_appointments': [serialize_model(a) for a in recent_appointments],
            'recent_emergencies': [serialize_model(e) for e in recent_emergencies]
        }
        
        return create_success_response(
            'Admin dashboard retrieved successfully',
            dashboard_data
        )
        
    except Exception as e:
        return create_error_response(f'Admin dashboard error: {str(e)}', status_code=500)


def get_hospital_dashboard(hospital_id):
    """Get hospital dashboard data"""
    try:
        from app.models import Hospital_info
        hospital_info = Hospital_info.query.get(hospital_id)
        if not hospital_info or not hospital_info.hospital:
            return create_error_response('Hospital not found', status_code=404)
        
        hospital = hospital_info.hospital
        
        stats = {
            'total_appointments': Appointment.query.filter_by(hospital_id=hospital.id).count(),
            'total_floors': hospital.floors.count(),
            'total_wards': sum(floor.wards.count() for floor in hospital.floors),
            'total_beds': sum(bed_count for floor in hospital.floors 
                            for ward in floor.wards 
                            for bed_count in [ward.beds.count()])
        }
        
        dashboard_data = {
            'hospital': serialize_model(hospital),
            'stats': stats
        }
        
        return create_success_response(
            'Hospital dashboard retrieved successfully',
            dashboard_data
        )
        
    except Exception as e:
        return create_error_response(f'Hospital dashboard error: {str(e)}', status_code=500)


def get_doctor_dashboard(user_id):
    """Get doctor dashboard data"""
    try:
        user = Users.query.get(user_id)
        if not user:
            return create_error_response('User not found', status_code=404)
        
        # Get doctor's appointments
        appointments = Appointment.query.filter_by(doctor_id=user_id).order_by(
            Appointment.scheduled_time.desc()
        ).limit(10).all()
        
        stats = {
            'total_appointments': Appointment.query.filter_by(doctor_id=user_id).count(),
            'upcoming_appointments': Appointment.query.filter(
                Appointment.doctor_id == user_id,
                Appointment.scheduled_time > db.func.now()
            ).count()
        }
        
        dashboard_data = {
            'user': serialize_model(user, exclude=['password']),
            'stats': stats,
            'recent_appointments': [serialize_model(a) for a in appointments]
        }
        
        return create_success_response(
            'Doctor dashboard retrieved successfully',
            dashboard_data
        )
        
    except Exception as e:
        return create_error_response(f'Doctor dashboard error: {str(e)}', status_code=500)


def get_user_dashboard(user_id):
    """Get regular user dashboard data"""
    try:
        user = Users.query.get(user_id)
        if not user:
            return create_error_response('User not found', status_code=404)
        
        # Get user's appointments
        appointments = Appointment.query.filter_by(patient_id=user_id).order_by(
            Appointment.scheduled_time.desc()
        ).limit(5).all()
        
        stats = {
            'total_appointments': Appointment.query.filter_by(patient_id=user_id).count(),
            'upcoming_appointments': Appointment.query.filter(
                Appointment.patient_id == user_id,
                Appointment.scheduled_time > db.func.now()
            ).count()
        }
        
        dashboard_data = {
            'user': serialize_model(user, exclude=['password']),
            'stats': stats,
            'recent_appointments': [serialize_model(a) for a in appointments]
        }
        
        return create_success_response(
            'User dashboard retrieved successfully',
            dashboard_data
        )
        
    except Exception as e:
        return create_error_response(f'User dashboard error: {str(e)}', status_code=500)
