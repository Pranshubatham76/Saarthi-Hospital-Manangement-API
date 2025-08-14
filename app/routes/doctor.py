from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import db, Doctors_Info, DoctorSchedule, Hospital
from app.auth.decorators import admin_required, doctor_or_admin_required
from app.utils.helpers import (
    serialize_model, create_success_response, create_error_response,
    validate_email
)

doctor_bp = Blueprint('doctor', __name__)


@doctor_bp.route('/register', methods=['POST'])
@admin_required
def register_doctor():
    """Register a new doctor"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'mail']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', status_code=400)
        
        if not validate_email(data['mail']):
            return create_error_response('Invalid email format', status_code=400)
        
        if Doctors_Info.query.filter_by(mail=data['mail']).first():
            return create_error_response('Email already registered', status_code=409)
        
        doctor = Doctors_Info(
            name=data['name'],
            specialisation=data.get('specialisation'),
            availability=data.get('availability'),
            mail=data['mail'],
            phone=data.get('phone')
        )
        
        db.session.add(doctor)
        db.session.commit()
        
        doctor_data = serialize_model(doctor)
        
        return create_success_response(
            'Doctor registered successfully',
            {'doctor': doctor_data},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Doctor registration failed: {str(e)}', status_code=500)


@doctor_bp.route('/all', methods=['GET'])
def get_all_doctors():
    """Get all doctors"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        specialisation = request.args.get('specialisation')
        
        query = Doctors_Info.query
        
        if specialisation:
            query = query.filter(Doctors_Info.specialisation.ilike(f'%{specialisation}%'))
        
        query = query.order_by(Doctors_Info.name)
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        doctors = []
        for doctor in pagination.items:
            doctors.append(serialize_model(doctor))
        
        return create_success_response(
            'Doctors retrieved successfully',
            {
                'doctors': doctors,
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
        return create_error_response(f'Failed to retrieve doctors: {str(e)}', status_code=500)


@doctor_bp.route('/<int:doctor_id>', methods=['GET'])
def get_doctor(doctor_id):
    """Get doctor details"""
    try:
        doctor = Doctors_Info.query.get(doctor_id)
        if not doctor:
            return create_error_response('Doctor not found', status_code=404)
        
        doctor_data = serialize_model(doctor)
        
        # Add hospital associations
        hospitals = []
        for hospital in doctor.hospitals:
            hospitals.append(serialize_model(hospital))
        doctor_data['hospitals'] = hospitals
        
        return create_success_response(
            'Doctor details retrieved successfully',
            {'doctor': doctor_data}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve doctor: {str(e)}', status_code=500)


@doctor_bp.route('/schedule', methods=['POST'])
@doctor_or_admin_required
def create_doctor_schedule():
    """Create doctor schedule"""
    try:
        data = request.get_json()
        
        required_fields = ['doctor_id', 'hospital_id']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', status_code=400)
        
        # Verify doctor and hospital exist
        doctor = Doctors_Info.query.get(data['doctor_id'])
        if not doctor:
            return create_error_response('Doctor not found', status_code=404)
        
        hospital = Hospital.query.get(data['hospital_id'])
        if not hospital:
            return create_error_response('Hospital not found', status_code=404)
        
        schedule = DoctorSchedule(
            doctor_id=data['doctor_id'],
            hospital_id=data['hospital_id'],
            day_of_week=data.get('day_of_week'),
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            specific_date=data.get('specific_date'),
            notes=data.get('notes')
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        schedule_data = serialize_model(schedule)
        
        return create_success_response(
            'Doctor schedule created successfully',
            {'schedule': schedule_data},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Schedule creation failed: {str(e)}', status_code=500)


@doctor_bp.route('/<int:doctor_id>/schedule', methods=['GET'])
def get_doctor_schedule(doctor_id):
    """Get doctor's schedule"""
    try:
        doctor = Doctors_Info.query.get(doctor_id)
        if not doctor:
            return create_error_response('Doctor not found', status_code=404)
        
        schedules = []
        for schedule in doctor.schedules:
            schedule_data = serialize_model(schedule)
            if schedule.hospital:
                schedule_data['hospital'] = serialize_model(schedule.hospital)
            schedules.append(schedule_data)
        
        return create_success_response(
            'Doctor schedule retrieved successfully',
            {'schedules': schedules}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve schedule: {str(e)}', status_code=500)
