from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import db, Emergency, Hospital, Ambulance, AmbulanceStatus
from app.auth.decorators import admin_required, api_key_required
from app.utils.helpers import (
    serialize_model, create_success_response, create_error_response,
    save_uploaded_file
)

emergency_bp = Blueprint('emergency', __name__)


@emergency_bp.route('/call', methods=['POST'])
def log_emergency():
    """Log an emergency request"""
    try:
        data = request.get_json()
        
        required_fields = ['emergency_type', 'location', 'contact_number']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', status_code=400)
        
        emergency = Emergency(
            emergency_type=data['emergency_type'],
            location=data['location'],
            contact_number=data['contact_number'],
            details=data.get('details'),
            hospital_id=data.get('hospital_id'),
            user_id=data.get('user_id'),
            user_ip=request.remote_addr
        )
        
        db.session.add(emergency)
        db.session.commit()
        
        emergency_data = serialize_model(emergency)
        
        return create_success_response(
            'Emergency logged successfully',
            {'emergency': emergency_data},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Failed to log emergency: {str(e)}', status_code=500)


@emergency_bp.route('/all', methods=['GET'])
@admin_required
def get_all_emergencies():
    """Get all emergency cases"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        emergency_type = request.args.get('type')
        status = request.args.get('status')
        
        query = Emergency.query
        
        if emergency_type:
            query = query.filter(Emergency.emergency_type.ilike(f'%{emergency_type}%'))
        
        if status:
            query = query.filter(Emergency.forward_status == status)
        
        query = query.order_by(Emergency.created_at.desc())
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        emergencies = []
        for emergency in pagination.items:
            emergency_data = serialize_model(emergency)
            
            if emergency.hospital:
                emergency_data['hospital'] = serialize_model(emergency.hospital)
            if emergency.user:
                emergency_data['user'] = serialize_model(emergency.user, exclude=['password'])
            
            emergencies.append(emergency_data)
        
        return create_success_response(
            'Emergencies retrieved successfully',
            {
                'emergencies': emergencies,
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
        return create_error_response(f'Failed to retrieve emergencies: {str(e)}', status_code=500)


@emergency_bp.route('/update/<int:case_id>', methods=['PUT'])
@admin_required
def update_emergency(case_id):
    """Update emergency case status"""
    try:
        emergency = Emergency.query.get(case_id)
        if not emergency:
            return create_error_response('Emergency case not found', status_code=404)
        
        data = request.get_json()
        
        if 'forward_status' in data:
            emergency.forward_status = data['forward_status']
        
        if 'forwarded_to_org' in data:
            emergency.forwarded_to_org = data['forwarded_to_org']
        
        if 'hospital_id' in data:
            emergency.hospital_id = data['hospital_id']
        
        db.session.commit()
        
        emergency_data = serialize_model(emergency)
        
        return create_success_response(
            'Emergency case updated successfully',
            {'emergency': emergency_data}
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Failed to update emergency: {str(e)}', status_code=500)


@emergency_bp.route('/ambulances/available', methods=['GET'])
def get_available_ambulances():
    """Get available ambulances"""
    try:
        hospital_id = request.args.get('hospital_id', type=int)
        ambulance_type = request.args.get('type')
        
        query = Ambulance.query.filter_by(status=AmbulanceStatus.VACANT)
        
        if hospital_id:
            query = query.filter_by(hospital_id=hospital_id)
        
        if ambulance_type:
            query = query.filter_by(type=ambulance_type)
        
        ambulances = []
        for ambulance in query.all():
            ambulance_data = serialize_model(ambulance)
            if ambulance.hospital:
                ambulance_data['hospital'] = serialize_model(ambulance.hospital)
            ambulances.append(ambulance_data)
        
        return create_success_response(
            'Available ambulances retrieved successfully',
            {'ambulances': ambulances}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve ambulances: {str(e)}', status_code=500)
