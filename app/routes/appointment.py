from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from app.models import (
    db, Appointment, AppointmentStatus, OPD, opdSlots, 
    OPDSlotReservation, Hospital, Doctors_Info, Users
)
from app.auth.decorators import token_required, doctor_or_admin_required
from app.utils.helpers import (
    serialize_model, create_success_response, create_error_response,
    generate_appointment_id, generate_opd_slot_id
)

appointment_bp = Blueprint('appointment', __name__)


@appointment_bp.route('/opd/book', methods=['POST'])
@jwt_required()
def book_opd_appointment():
    """Book an OPD appointment"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        required_fields = ['hospital_id', 'slot_id']
        for field in required_fields:
            if field not in data:
                return create_error_response(f'{field} is required', status_code=400)
        
        # Verify hospital exists
        hospital = Hospital.query.get(data['hospital_id'])
        if not hospital:
            return create_error_response('Hospital not found', status_code=404)
        
        # Verify slot exists and is available
        slot = opdSlots.query.get(data['slot_id'])
        if not slot:
            return create_error_response('OPD slot not found', status_code=404)
        
        # Check if slot has capacity
        if slot.occupancy >= slot.capacity:
            return create_error_response('OPD slot is fully booked', status_code=409)
        
        # Check if slot is in the future
        if slot.slot_start <= datetime.utcnow():
            return create_error_response('Cannot book past slots', status_code=400)
        
        # Check if user already has an appointment for this slot
        existing_appointment = Appointment.query.filter_by(
            patient_id=current_user_id,
            slot_id=data['slot_id'],
            status=AppointmentStatus.CONFIRMED
        ).first()
        
        if existing_appointment:
            return create_error_response('You already have an appointment for this slot', status_code=409)
        
        # Create appointment
        appointment = Appointment(
            appointment_type='opd',
            patient_id=current_user_id,
            hospital_id=data['hospital_id'],
            doctor_id=slot.doctor_id,
            slot_id=data['slot_id'],
            booked_by_user_id=current_user_id,
            status=AppointmentStatus.CONFIRMED,
            scheduled_time=slot.slot_start,
            reason=data.get('reason')
        )
        
        # Create slot reservation
        reservation = OPDSlotReservation(
            slot_id=data['slot_id'],
            user_id=current_user_id,
            reason=data.get('reason')
        )
        
        # Update slot occupancy
        slot.occupancy += 1
        
        db.session.add(appointment)
        db.session.add(reservation)
        db.session.commit()
        
        appointment_data = serialize_model(appointment)
        
        # Add related data
        if appointment.patient:
            appointment_data['patient'] = serialize_model(appointment.patient, exclude=['password'])
        if appointment.doctor:
            appointment_data['doctor'] = serialize_model(appointment.doctor)
        if appointment.hospital:
            appointment_data['hospital'] = serialize_model(appointment.hospital)
        if appointment.slot:
            appointment_data['slot'] = serialize_model(appointment.slot)
        
        return create_success_response(
            'OPD appointment booked successfully',
            {'appointment': appointment_data},
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Appointment booking failed: {str(e)}', status_code=500)


@appointment_bp.route('/opd/<int:appointment_id>', methods=['GET'])
@jwt_required()
def get_opd_appointment(appointment_id):
    """Get OPD appointment details"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role')
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return create_error_response('Appointment not found', status_code=404)
        
        # Check access permissions
        if (appointment.patient_id != current_user_id and 
            user_role not in ['admin', 'doctor', 'hospital_admin']):
            return create_error_response('Access denied', status_code=403)
        
        appointment_data = serialize_model(appointment)
        
        # Add related data
        if appointment.patient:
            appointment_data['patient'] = serialize_model(appointment.patient, exclude=['password'])
        if appointment.doctor:
            appointment_data['doctor'] = serialize_model(appointment.doctor)
        if appointment.hospital:
            appointment_data['hospital'] = serialize_model(appointment.hospital)
        if appointment.slot:
            appointment_data['slot'] = serialize_model(appointment.slot)
        
        return create_success_response(
            'Appointment details retrieved successfully',
            {'appointment': appointment_data}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve appointment: {str(e)}', status_code=500)


@appointment_bp.route('/opd/update/<int:appointment_id>', methods=['PUT'])
@jwt_required()
def update_opd_appointment(appointment_id):
    """Update OPD appointment"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role')
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return create_error_response('Appointment not found', status_code=404)
        
        # Check permissions - only patient or admin/doctor can update
        if (appointment.patient_id != current_user_id and 
            user_role not in ['admin', 'doctor', 'hospital_admin']):
            return create_error_response('Access denied', status_code=403)
        
        data = request.get_json()
        
        # Update status if provided
        if 'status' in data:
            try:
                new_status = AppointmentStatus(data['status'])
                old_status = appointment.status
                appointment.status = new_status
                
                # If cancelling appointment, free up the slot
                if (new_status == AppointmentStatus.CANCELLED and 
                    old_status in [AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]):
                    
                    if appointment.slot:
                        appointment.slot.occupancy = max(0, appointment.slot.occupancy - 1)
                        
                        # Remove reservation
                        reservation = OPDSlotReservation.query.filter_by(
                            slot_id=appointment.slot_id,
                            user_id=appointment.patient_id
                        ).first()
                        if reservation:
                            db.session.delete(reservation)
                
            except ValueError:
                return create_error_response(
                    f'Invalid status. Allowed values: {[e.value for e in AppointmentStatus]}',
                    status_code=400
                )
        
        # Update reason if provided
        if 'reason' in data:
            appointment.reason = data['reason']
        
        db.session.commit()
        
        appointment_data = serialize_model(appointment)
        
        return create_success_response(
            'Appointment updated successfully',
            {'appointment': appointment_data}
        )
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Appointment update failed: {str(e)}', status_code=500)


@appointment_bp.route('/opd/cancel/<int:appointment_id>', methods=['DELETE'])
@jwt_required()
def cancel_opd_appointment(appointment_id):
    """Cancel OPD appointment"""
    try:
        current_user_id = get_jwt_identity()
        claims = get_jwt()
        user_role = claims.get('role')
        
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return create_error_response('Appointment not found', status_code=404)
        
        # Check permissions
        if (appointment.patient_id != current_user_id and 
            user_role not in ['admin', 'hospital_admin']):
            return create_error_response('Access denied', status_code=403)
        
        # Can only cancel confirmed or pending appointments
        if appointment.status not in [AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]:
            return create_error_response(
                f'Cannot cancel appointment with status: {appointment.status.value}',
                status_code=400
            )
        
        # Update appointment status
        appointment.status = AppointmentStatus.CANCELLED
        
        # Free up slot capacity
        if appointment.slot:
            appointment.slot.occupancy = max(0, appointment.slot.occupancy - 1)
            
            # Remove reservation
            reservation = OPDSlotReservation.query.filter_by(
                slot_id=appointment.slot_id,
                user_id=appointment.patient_id
            ).first()
            if reservation:
                db.session.delete(reservation)
        
        db.session.commit()
        
        return create_success_response('Appointment cancelled successfully')
        
    except Exception as e:
        db.session.rollback()
        return create_error_response(f'Appointment cancellation failed: {str(e)}', status_code=500)


@appointment_bp.route('/my-appointments', methods=['GET'])
@jwt_required()
def get_my_appointments():
    """Get current user's appointments"""
    try:
        current_user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status_filter = request.args.get('status')
        appointment_type = request.args.get('type')
        
        query = Appointment.query.filter_by(patient_id=current_user_id)
        
        # Apply filters
        if status_filter:
            try:
                query = query.filter_by(status=AppointmentStatus(status_filter))
            except ValueError:
                return create_error_response('Invalid status filter', status_code=400)
        
        if appointment_type:
            query = query.filter_by(appointment_type=appointment_type)
        
        # Order by scheduled time (newest first)
        query = query.order_by(Appointment.scheduled_time.desc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        appointments = []
        for appointment in pagination.items:
            appointment_data = serialize_model(appointment)
            
            # Add related data
            if appointment.doctor:
                appointment_data['doctor'] = serialize_model(appointment.doctor)
            if appointment.hospital:
                appointment_data['hospital'] = serialize_model(appointment.hospital)
            if appointment.slot:
                appointment_data['slot'] = serialize_model(appointment.slot)
            
            appointments.append(appointment_data)
        
        return create_success_response(
            'Appointments retrieved successfully',
            {
                'appointments': appointments,
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
        return create_error_response(f'Failed to retrieve appointments: {str(e)}', status_code=500)


@appointment_bp.route('/hospital/<int:hospital_id>/appointments', methods=['GET'])
@doctor_or_admin_required
def get_hospital_appointments(hospital_id):
    """Get hospital appointments (for hospital staff)"""
    try:
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return create_error_response('Hospital not found', status_code=404)
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        date_filter = request.args.get('date')  # YYYY-MM-DD format
        
        query = Appointment.query.filter_by(hospital_id=hospital_id)
        
        # Apply filters
        if status_filter:
            try:
                query = query.filter_by(status=AppointmentStatus(status_filter))
            except ValueError:
                return create_error_response('Invalid status filter', status_code=400)
        
        if date_filter:
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                query = query.filter(
                    db.func.date(Appointment.scheduled_time) == filter_date
                )
            except ValueError:
                return create_error_response('Invalid date format. Use YYYY-MM-DD', status_code=400)
        
        # Order by scheduled time
        query = query.order_by(Appointment.scheduled_time.asc())
        
        # Paginate
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        appointments = []
        for appointment in pagination.items:
            appointment_data = serialize_model(appointment)
            
            # Add related data
            if appointment.patient:
                appointment_data['patient'] = serialize_model(appointment.patient, exclude=['password'])
            if appointment.doctor:
                appointment_data['doctor'] = serialize_model(appointment.doctor)
            if appointment.slot:
                appointment_data['slot'] = serialize_model(appointment.slot)
            
            appointments.append(appointment_data)
        
        return create_success_response(
            'Hospital appointments retrieved successfully',
            {
                'appointments': appointments,
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
        return create_error_response(f'Failed to retrieve appointments: {str(e)}', status_code=500)


@appointment_bp.route('/available-slots', methods=['GET'])
def get_available_slots():
    """Get available OPD slots"""
    try:
        hospital_id = request.args.get('hospital_id', type=int)
        doctor_id = request.args.get('doctor_id', type=int)
        department = request.args.get('department')
        date_str = request.args.get('date')  # YYYY-MM-DD format
        
        if not hospital_id:
            return create_error_response('hospital_id is required', status_code=400)
        
        # Verify hospital exists
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return create_error_response('Hospital not found', status_code=404)
        
        # Build query
        query = opdSlots.query.join(OPD).filter(OPD.hospital_id == hospital_id)
        
        # Add filters
        if doctor_id:
            query = query.filter(opdSlots.doctor_id == doctor_id)
        
        if department:
            query = query.filter(OPD.department.ilike(f'%{department}%'))
        
        if date_str:
            try:
                filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                query = query.filter(
                    db.func.date(opdSlots.slot_start) == filter_date
                )
            except ValueError:
                return create_error_response('Invalid date format. Use YYYY-MM-DD', status_code=400)
        
        # Only show future slots with available capacity
        query = query.filter(
            opdSlots.slot_start > datetime.utcnow(),
            opdSlots.occupancy < opdSlots.capacity
        ).order_by(opdSlots.slot_start.asc())
        
        slots = []
        for slot in query.limit(50):  # Limit to prevent large responses
            slot_data = serialize_model(slot)
            
            # Add related data
            if slot.doctor:
                slot_data['doctor'] = serialize_model(slot.doctor)
            if slot.opd:
                slot_data['opd'] = serialize_model(slot.opd)
            
            slot_data['available_capacity'] = slot.capacity - slot.occupancy
            slots.append(slot_data)
        
        return create_success_response(
            'Available slots retrieved successfully',
            {'slots': slots}
        )
        
    except Exception as e:
        return create_error_response(f'Failed to retrieve slots: {str(e)}', status_code=500)
