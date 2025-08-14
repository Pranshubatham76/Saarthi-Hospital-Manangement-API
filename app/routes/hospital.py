from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import (
    db, Hospital, Hospital_info, Floor, Ward, WardCategory, Bed,
    BedStatus, OPDStatus
)
from app.auth.decorators import admin_required, hospital_admin_or_admin_required
from app.utils.helpers import (
    hash_password, validate_email, serialize_model,
    create_success_response, create_error_response,
    generate_hospital_registration_id, check_password,
    validate_password_strength
)

hospital_bp = Blueprint('hospital', __name__)


@hospital_bp.route('/register', methods=['POST'])
@admin_required
def register_hospital():
    """Register a new hospital"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'name', 'type', 'email', 'password', 'location']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', status_code=400)
        
        # Validate email format
        if not validate_email(data['email']):
            return create_error_response('Invalid email format', status_code=400)
        
        # Check if hospital already exists
        if Hospital_info.query.filter_by(username=data['username']).first():
            return create_error_response('Username already exists', status_code=409)
        
        if Hospital_info.query.filter_by(email=data['email']).first():
            return create_error_response('Email already registered', status_code=409)
        
        # Generate registration ID if not provided
        reg_id = data.get('reg_id') or generate_hospital_registration_id()
        
        if Hospital_info.query.filter_by(reg_id=reg_id).first():
            return create_error_response('Registration ID already exists', status_code=409)
        
        # Hash password
        hashed_password = hash_password(data['password'])
        
        # Create hospital info
        hospital_info = Hospital_info(
            username=data['username'],
            name=data['name'],
            type=data['type'],
            email=data['email'],
            password=hashed_password,
            location=data['location'],
            is_multi_level=data.get('is_multi_level', False),
            reg_id=reg_id,
            availability=data.get('availability')
        )
        
        # Create associated hospital record
        hospital = Hospital(
            name=data['name'],
            location=data['location'],
            contact_num=data.get('contact_num'),
            email=data['email'],
            hospital_type=data['type'],
            bedAvailability=data.get('bedAvailability', 0),
            oxygenUnits=data.get('oxygenUnits', 0)
        )
        
        db.session.add(hospital_info)
        db.session.flush()  # Get the ID
        
        hospital.hospital_info_id = hospital_info.id
        db.session.add(hospital)
        
        # If single-level hospital, create default floor and ward
        if not hospital_info.is_multi_level:
            db.session.flush()  # Get hospital ID
            
            floor = Floor(
                floor_number='0',
                floor_name='Ground Floor',
                hospital_id=hospital.id
            )
            db.session.add(floor)
            db.session.flush()
            
            # Create default ward category if it doesn't exist
            general_category = WardCategory.query.filter_by(name='General').first()
            if not general_category:
                general_category = WardCategory(
                    name='General',
                    description='General ward for regular patients'
                )
                db.session.add(general_category)
                db.session.flush()
            
            # Create default ward
            ward = Ward(
                ward_number='W1',
                category_id=general_category.id,
                capacity=data.get('default_ward_capacity', 10),
                floor_id=floor.id
            )
            db.session.add(ward)
        
        db.session.commit()
        
        hospital_data = serialize_model(hospital_info, exclude=['password'])
        
        return create_success_response(
            'Hospital registered successfully',
            {'hospital': hospital_data},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Hospital registration failed: {str(e)}', status_code=500)


@hospital_bp.route('/all', methods=['GET'])
def get_all_hospitals():
    """Get all hospitals"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        hospital_type = request.args.get('type')
        location = request.args.get('location')
        
        query = Hospital.query
        
        # Apply filters
        if hospital_type:
            query = query.filter(Hospital.hospital_type == hospital_type)
        
        if location:
            query = query.filter(Hospital.location.ilike(f'%{location}%'))
        
        # Order by name
        query = query.order_by(Hospital.name)
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        hospitals = []
        for hospital in pagination.items:
            hospital_data = serialize_model(hospital)
            
            # Add hospital info if available
            if hospital.hospital_info:
                hospital_data['hospital_info'] = serialize_model(
                    hospital.hospital_info, 
                    exclude=['password']
                )
            
            hospitals.append(hospital_data)
        
        return create_success_response(
            'Hospitals retrieved successfully',
            {
                'hospitals': hospitals,
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
        return create_error_response(f'Failed to retrieve hospitals: {str(e)}', status_code=500)


@hospital_bp.route('/<int:hospital_id>', methods=['GET'])
def get_hospital(hospital_id):
    """Get hospital details"""
    try:
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return create_error_response('Hospital not found', status_code=404)
        
        hospital_data = serialize_model(hospital)
        
        # Add hospital info
        if hospital.hospital_info:
            hospital_data['hospital_info'] = serialize_model(
                hospital.hospital_info, 
                exclude=['password']
            )
        
        # Add floor and ward counts
        hospital_data['floor_count'] = hospital.floors.count()
        hospital_data['total_wards'] = sum(floor.wards.count() for floor in hospital.floors)
        hospital_data['total_beds'] = sum(
            bed_count for floor in hospital.floors 
            for ward in floor.wards 
            for bed_count in [ward.beds.count()]
        )
        
        return create_success_response(
            'Hospital details retrieved successfully',
            {'hospital': hospital_data}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve hospital: {str(e)}', status_code=500)


@hospital_bp.route('/update/<int:hospital_id>', methods=['PUT'])
@hospital_admin_or_admin_required
def update_hospital(hospital_id):
    """Update hospital details"""
    try:
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return create_error_response('Hospital not found', status_code=404)
        
        # Check if current user can update this hospital
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role')
        user_type = claims.get('type')
        
        # If hospital admin, check if they own this hospital
        if user_type == 'hospital' and hospital.hospital_info_id != current_user_id:
            return create_error_response('Access denied', status_code=403)
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            hospital.name = data['name']
        
        if 'location' in data:
            hospital.location = data['location']
        
        if 'contact_num' in data:
            hospital.contact_num = data['contact_num']
        
        if 'hospital_type' in data:
            hospital.hospital_type = data['hospital_type']
        
        if 'bedAvailability' in data:
            hospital.bedAvailability = data['bedAvailability']
        
        if 'oxygenUnits' in data:
            hospital.oxygenUnits = data['oxygenUnits']
        
        if 'opd_status' in data:
            try:
                hospital.opd_status = OPDStatus(data['opd_status'])
            except ValueError:
                return create_error_response(
                    f'Invalid OPD status. Allowed values: {[e.value for e in OPDStatus]}',
                    status_code=400
                )
        
        # Update hospital_info if provided and user has permission
        if hospital.hospital_info and 'hospital_info' in data:
            info_data = data['hospital_info']
            
            if 'name' in info_data:
                hospital.hospital_info.name = info_data['name']
            
            if 'type' in info_data:
                hospital.hospital_info.type = info_data['type']
            
            if 'location' in info_data:
                hospital.hospital_info.location = info_data['location']
            
            if 'availability' in info_data:
                hospital.hospital_info.availability = info_data['availability']
        
        db.session.commit()
        
        hospital_data = serialize_model(hospital)
        if hospital.hospital_info:
            hospital_data['hospital_info'] = serialize_model(
                hospital.hospital_info, 
                exclude=['password']
            )
        
        return create_success_response(
            'Hospital updated successfully',
            {'hospital': hospital_data}
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Hospital update failed: {str(e)}', status_code=500)


@hospital_bp.route('/delete/<int:hospital_id>', methods=['DELETE'])
@admin_required
def delete_hospital(hospital_id):
    """Delete hospital (admin only)"""
    try:
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return create_error_response('Hospital not found', status_code=404)
        
        hospital_name = hospital.name
        
        # Delete associated hospital_info as well
        if hospital.hospital_info:
            db.session.delete(hospital.hospital_info)
        
        db.session.delete(hospital)
        db.session.commit()
        
        return create_success_response(f'Hospital "{hospital_name}" deleted successfully')
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Hospital deletion failed: {str(e)}', status_code=500)


# Floor Management Routes

@hospital_bp.route('/<int:hospital_id>/floors/create', methods=['POST'])
@hospital_admin_or_admin_required
def create_floor(hospital_id):
    """Create a new floor for a hospital"""
    try:
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return create_error_response('Hospital not found', status_code=404)
        
        # Check if current user can manage this hospital
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_type = claims.get('type')
        
        if user_type == 'hospital' and hospital.hospital_info_id != current_user_id:
            return create_error_response('Access denied', status_code=403)
        
        # Check if hospital is multi-level
        if hospital.hospital_info and not hospital.hospital_info.is_multi_level:
            return create_error_response(
                'Cannot create multiple floors for single-level hospital',
                status_code=400
            )
        
        data = request.get_json()
        
        if not data.get('floor_number'):
            return create_error_response('Floor number is required', status_code=400)
        
        # Check if floor already exists
        existing_floor = Floor.query.filter_by(
            hospital_id=hospital_id,
            floor_number=data['floor_number']
        ).first()
        
        if existing_floor:
            return create_error_response('Floor number already exists', status_code=409)
        
        floor = Floor(
            floor_number=data['floor_number'],
            floor_name=data.get('floor_name'),
            hospital_id=hospital_id
        )
        
        db.session.add(floor)
        db.session.commit()
        
        floor_data = serialize_model(floor)
        
        return create_success_response(
            'Floor created successfully',
            {'floor': floor_data},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Floor creation failed: {str(e)}', status_code=500)


@hospital_bp.route('/<int:hospital_id>/floors', methods=['GET'])
def get_hospital_floors(hospital_id):
    """Get all floors of a hospital"""
    try:
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return create_error_response('Hospital not found', status_code=404)
        
        floors = []
        for floor in hospital.floors.order_by(Floor.floor_number):
            floor_data = serialize_model(floor)
            floor_data['ward_count'] = floor.wards.count()
            floors.append(floor_data)
        
        return create_success_response(
            'Hospital floors retrieved successfully',
            {'floors': floors}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve floors: {str(e)}', status_code=500)


# Ward Management Routes

@hospital_bp.route('/ward/create', methods=['POST'])
@hospital_admin_or_admin_required
def create_ward():
    """Create a ward"""
    try:
        data = request.get_json()
        
        required_fields = ['ward_number', 'floor_id', 'capacity']
        for field in required_fields:
            if field not in data:
                return create_error_response(f'{field} is required', status_code=400)
        
        floor = Floor.query.get(data['floor_id'])
        if not floor:
            return create_error_response('Floor not found', status_code=404)
        
        # Check permissions
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_type = claims.get('type')
        
        if user_type == 'hospital' and floor.hospital.hospital_info_id != current_user_id:
            return create_error_response('Access denied', status_code=403)
        
        # Check if ward number already exists on this floor
        existing_ward = Ward.query.filter_by(
            floor_id=data['floor_id'],
            ward_number=data['ward_number']
        ).first()
        
        if existing_ward:
            return create_error_response('Ward number already exists on this floor', status_code=409)
        
        ward = Ward(
            ward_number=data['ward_number'],
            category_id=data.get('category_id'),
            capacity=data['capacity'],
            floor_id=data['floor_id']
        )
        
        db.session.add(ward)
        db.session.commit()
        
        ward_data = serialize_model(ward)
        if ward.category:
            ward_data['category'] = serialize_model(ward.category)
        
        return create_success_response(
            'Ward created successfully',
            {'ward': ward_data},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Ward creation failed: {str(e)}', status_code=500)


@hospital_bp.route('/ward/<int:ward_id>', methods=['GET'])
def get_ward(ward_id):
    """Get ward details"""
    try:
        ward = Ward.query.get(ward_id)
        if not ward:
            return create_error_response('Ward not found', status_code=404)
        
        ward_data = serialize_model(ward)
        
        if ward.category:
            ward_data['category'] = serialize_model(ward.category)
        
        if ward.floor:
            ward_data['floor'] = serialize_model(ward.floor)
        
        ward_data['bed_count'] = ward.beds.count()
        ward_data['occupied_beds'] = ward.beds.filter_by(status=BedStatus.OCCUPIED).count()
        ward_data['available_beds'] = ward.beds.filter_by(status=BedStatus.VACANT).count()
        
        return create_success_response(
            'Ward details retrieved successfully',
            {'ward': ward_data}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve ward: {str(e)}', status_code=500)


@hospital_bp.route('/<int:hospital_id>/wards', methods=['GET'])
def get_hospital_wards(hospital_id):
    """Get all wards of a hospital"""
    try:
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return create_error_response('Hospital not found', status_code=404)
        
        wards = []
        for floor in hospital.floors:
            for ward in floor.wards:
                ward_data = serialize_model(ward)
                ward_data['floor'] = serialize_model(floor)
                if ward.category:
                    ward_data['category'] = serialize_model(ward.category)
                ward_data['bed_count'] = ward.beds.count()
                wards.append(ward_data)
        
        return create_success_response(
            'Hospital wards retrieved successfully',
            {'wards': wards}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve wards: {str(e)}', status_code=500)


# Bed Management Routes

@hospital_bp.route('/ward/<int:ward_id>/bed/create', methods=['POST'])
@hospital_admin_or_admin_required
def create_bed(ward_id):
    """Add a bed to a ward"""
    try:
        ward = Ward.query.get(ward_id)
        if not ward:
            return create_error_response('Ward not found', status_code=404)
        
        # Check permissions
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_type = claims.get('type')
        
        if user_type == 'hospital' and ward.floor.hospital.hospital_info_id != current_user_id:
            return create_error_response('Access denied', status_code=403)
        
        data = request.get_json()
        
        if not data.get('bed_number'):
            return create_error_response('Bed number is required', status_code=400)
        
        # Check if bed number already exists in this ward
        existing_bed = Bed.query.filter_by(
            ward_id=ward_id,
            bed_number=data['bed_number']
        ).first()
        
        if existing_bed:
            return create_error_response('Bed number already exists in this ward', status_code=409)
        
        bed = Bed(
            ward_id=ward_id,
            bed_number=data['bed_number'],
            bed_type=data.get('bed_type', 'General'),
            status=BedStatus.VACANT
        )
        
        db.session.add(bed)
        db.session.commit()
        
        bed_data = serialize_model(bed)
        
        return create_success_response(
            'Bed created successfully',
            {'bed': bed_data},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Bed creation failed: {str(e)}', status_code=500)


@hospital_bp.route('/ward/<int:ward_id>/beds', methods=['GET'])
def get_ward_beds(ward_id):
    """Get all beds in a ward"""
    try:
        ward = Ward.query.get(ward_id)
        if not ward:
            return create_error_response('Ward not found', status_code=404)
        
        beds = []
        for bed in ward.beds.order_by(Bed.bed_number):
            beds.append(serialize_model(bed))
        
        return create_success_response(
            'Ward beds retrieved successfully',
            {'beds': beds}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve beds: {str(e)}', status_code=500)


@hospital_bp.route('/bed/<int:bed_id>', methods=['GET'])
def get_bed(bed_id):
    """Get bed details"""
    try:
        bed = Bed.query.get(bed_id)
        if not bed:
            return create_error_response('Bed not found', status_code=404)
        
        bed_data = serialize_model(bed)
        bed_data['ward'] = serialize_model(bed.ward)
        
        return create_success_response(
            'Bed details retrieved successfully',
            {'bed': bed_data}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve bed: {str(e)}', status_code=500)


@hospital_bp.route('/bed/update/<int:bed_id>', methods=['PUT'])
@hospital_admin_or_admin_required
def update_bed(bed_id):
    """Update bed details"""
    try:
        bed = Bed.query.get(bed_id)
        if not bed:
            return create_error_response('Bed not found', status_code=404)
        
        # Check permissions
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_type = claims.get('type')
        
        if user_type == 'hospital' and bed.ward.floor.hospital.hospital_info_id != current_user_id:
            return create_error_response('Access denied', status_code=403)
        
        data = request.get_json()
        
        if 'status' in data:
            try:
                bed.status = BedStatus(data['status'])
            except ValueError:
                return create_error_response(
                    f'Invalid bed status. Allowed values: {[e.value for e in BedStatus]}',
                    status_code=400
                )
        
        if 'bed_type' in data:
            bed.bed_type = data['bed_type']
        
        db.session.commit()
        
        bed_data = serialize_model(bed)
        
        return create_success_response(
            'Bed updated successfully',
            {'bed': bed_data}
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Bed update failed: {str(e)}', status_code=500)
