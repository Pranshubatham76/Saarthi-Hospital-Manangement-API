from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import (
    db, BloodBank, BloodInventory, ReserveBlood, StatusEnum, Hospital
)
from app.auth.decorators import admin_required, hospital_admin_or_admin_required
from app.utils.helpers import (
    serialize_model, create_success_response, create_error_response,
    validate_email
)

blood_bank_bp = Blueprint('blood_bank', __name__)


@blood_bank_bp.route('/register', methods=['POST'])
@admin_required
def register_blood_bank():
    """Register a new blood bank"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'location', 'contact_no', 'email']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', status_code=400)
        
        if not validate_email(data['email']):
            return create_error_response('Invalid email format', status_code=400)
        
        if BloodBank.query.filter_by(email=data['email']).first():
            return create_error_response('Email already registered', status_code=409)
        
        blood_bank = BloodBank(
            name=data['name'],
            location=data['location'],
            contact_no=data['contact_no'],
            email=data['email'],
            blood_types_available=data.get('blood_types_available', []),
            stock_levels=data.get('stock_levels', {}),
            category=data.get('category')
        )
        
        db.session.add(blood_bank)
        db.session.commit()
        
        blood_bank_data = serialize_model(blood_bank)
        
        return create_success_response(
            'Blood bank registered successfully',
            {'blood_bank': blood_bank_data},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Blood bank registration failed: {str(e)}', status_code=500)


@blood_bank_bp.route('/all', methods=['GET'])
def get_all_blood_banks():
    """Get all blood banks"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        location = request.args.get('location')
        blood_type = request.args.get('blood_type')
        
        query = BloodBank.query
        
        if location:
            query = query.filter(BloodBank.location.ilike(f'%{location}%'))
        
        if blood_type:
            query = query.filter(BloodBank.blood_types_available.any(blood_type))
        
        query = query.order_by(BloodBank.name)
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        blood_banks = []
        for blood_bank in pagination.items:
            blood_banks.append(serialize_model(blood_bank))
        
        return create_success_response(
            'Blood banks retrieved successfully',
            {
                'blood_banks': blood_banks,
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
        return create_error_response(f'Failed to retrieve blood banks: {str(e)}', status_code=500)


@blood_bank_bp.route('/<int:bloodbank_id>/addstock', methods=['POST'])
@admin_required
def add_blood_stock(bloodbank_id):
    """Add blood stock to a blood bank"""
    try:
        blood_bank = BloodBank.query.get(bloodbank_id)
        if not blood_bank:
            return create_error_response('Blood bank not found', status_code=404)
        
        data = request.get_json()
        
        required_fields = ['blood_type', 'units']
        for field in required_fields:
            if field not in data:
                return create_error_response(f'{field} is required', status_code=400)
        
        # Check if inventory already exists for this blood type and lot
        existing_inventory = BloodInventory.query.filter_by(
            bloodbank_id=bloodbank_id,
            blood_type=data['blood_type'],
            lot_number=data.get('lot_number')
        ).first()
        
        if existing_inventory:
            # Update existing inventory
            existing_inventory.units += data['units']
            if data.get('expiry_date'):
                existing_inventory.expiry_date = data['expiry_date']
        else:
            # Create new inventory record
            inventory = BloodInventory(
                bloodbank_id=bloodbank_id,
                blood_type=data['blood_type'],
                units=data['units'],
                expiry_date=data.get('expiry_date'),
                lot_number=data.get('lot_number')
            )
            db.session.add(inventory)
        
        # Update blood bank's available types if not already present
        if data['blood_type'] not in (blood_bank.blood_types_available or []):
            if blood_bank.blood_types_available:
                blood_bank.blood_types_available.append(data['blood_type'])
            else:
                blood_bank.blood_types_available = [data['blood_type']]
        
        # Update stock levels in blood bank
        if not blood_bank.stock_levels:
            blood_bank.stock_levels = {}
        
        current_stock = blood_bank.stock_levels.get(data['blood_type'], 0)
        blood_bank.stock_levels[data['blood_type']] = current_stock + data['units']
        
        db.session.commit()
        
        return create_success_response('Blood stock added successfully')
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Failed to add blood stock: {str(e)}', status_code=500)


@blood_bank_bp.route('/<int:bloodbank_id>/stock', methods=['GET'])
def get_blood_stock(bloodbank_id):
    """Get blood stock details for a blood bank"""
    try:
        blood_bank = BloodBank.query.get(bloodbank_id)
        if not blood_bank:
            return create_error_response('Blood bank not found', status_code=404)
        
        inventories = []
        for inventory in blood_bank.inventories:
            inventories.append(serialize_model(inventory))
        
        blood_bank_data = serialize_model(blood_bank)
        blood_bank_data['inventories'] = inventories
        
        return create_success_response(
            'Blood stock retrieved successfully',
            {'blood_bank': blood_bank_data}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve blood stock: {str(e)}', status_code=500)


@blood_bank_bp.route('/request', methods=['POST'])
@jwt_required()
def request_blood():
    """Request blood from blood banks"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['blood_group', 'quantity_units', 'location', 'reference']
        for field in required_fields:
            if not data.get(field):
                return create_error_response(f'{field} is required', status_code=400)
        
        # Create blood request
        blood_request = ReserveBlood(
            user_id=current_user_id,
            requester_name=data.get('requester_name', 'none'),
            requester_phone=data.get('requester_phone', 'none'),
            requester_email=data.get('requester_email', 'none'),
            blood_group=data['blood_group'],
            quantity_units=data['quantity_units'],
            location=data['location'],
            reference=data['reference'],
            bloodbank_id=data.get('bloodbank_id'),
            blood_inventory_id=data.get('blood_inventory_id'),
            status=StatusEnum.PENDING
        )
        
        db.session.add(blood_request)
        db.session.commit()
        
        request_data = serialize_model(blood_request)
        
        return create_success_response(
            'Blood request submitted successfully',
            {'request': request_data},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Blood request failed: {str(e)}', status_code=500)


@blood_bank_bp.route('/requests', methods=['GET'])
@jwt_required()
def get_blood_requests():
    """Get blood requests"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role')
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        
        # Admin can see all requests, users can see only their own
        if user_role == 'admin':
            query = ReserveBlood.query
        else:
            query = ReserveBlood.query.filter_by(user_id=current_user_id)
        
        if status_filter:
            try:
                query = query.filter_by(status=StatusEnum(status_filter))
            except ValueError:
                return create_error_response('Invalid status filter', status_code=400)
        
        query = query.order_by(ReserveBlood.created_at.desc())
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        requests = []
        for blood_request in pagination.items:
            request_data = serialize_model(blood_request)
            
            # Add related data
            if blood_request.user:
                request_data['user'] = serialize_model(blood_request.user, exclude=['password'])
            if blood_request.bloodbank:
                request_data['bloodbank'] = serialize_model(blood_request.bloodbank)
            
            requests.append(request_data)
        
        return create_success_response(
            'Blood requests retrieved successfully',
            {
                'requests': requests,
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
        return create_error_response(f'Failed to retrieve blood requests: {str(e)}', status_code=500)
