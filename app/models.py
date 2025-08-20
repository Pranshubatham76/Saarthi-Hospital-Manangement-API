# models.py
from datetime import datetime
import enum

from sqlalchemy import UniqueConstraint, event, text
from sqlalchemy.dialects.postgresql import JSON
from app import db

# ---------------------------
# ENUMS
# ---------------------------
class OPDStatus(enum.Enum):
    OPEN = "Open"
    CLOSED = "Closed"
    LIMITED = "Limited"

class StatusEnum(enum.Enum):
    PENDING = "pending"
    RESOLVED = "resolved"

class AppointmentStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class BedStatus(enum.Enum):
    VACANT = "vacant"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"

class AmbulanceStatus(enum.Enum):
    VACANT = "vacant"
    OCCUPIED = "occupied"
    UNAVAILABLE = "unavailable"

class AmbulanceType(enum.Enum):
    PUBLIC = "public"
    PRIVATE = "private"


# ---------------------------
# Association / Junction Tables
# ---------------------------
hospital_doctor = db.Table(
    'hospital_doctor',
    db.Column('hospital_id', db.Integer, db.ForeignKey('hospital.id', ondelete='CASCADE'), primary_key=True),
    db.Column('doctor_id', db.Integer, db.ForeignKey('doctors_info.id', ondelete='CASCADE'), primary_key=True)
)

bloodbank_hospital = db.Table(
    'bloodbank_hospital',
    db.Column('bloodbank_id', db.Integer, db.ForeignKey('blood_bank.id', ondelete='CASCADE'), primary_key=True),
    db.Column('hospital_id', db.Integer, db.ForeignKey('hospital.id', ondelete='CASCADE'), primary_key=True)
)


# ---------------------------
# USER & AUTH
# ---------------------------
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    fullname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # store hashed password
    phone_num = db.Column(db.String(30), nullable=True)
    location = db.Column(db.String(800), nullable=True)
    role = db.Column(db.String(50), nullable=False, default='user')  # user, doctor, hospital_admin, admin, donor, ambulance_driver
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    admin_logs = db.relationship('AdminLog', back_populates='user', lazy='dynamic')
    blood_requests = db.relationship('ReserveBlood', back_populates='user', lazy='dynamic')
    emergencies = db.relationship('Emergency', back_populates='user', lazy='dynamic')
    opd_reservations = db.relationship('OPDSlotReservation', back_populates='user', lazy='dynamic')
    appointments = db.relationship('Appointment', back_populates='patient', lazy='dynamic', foreign_keys='Appointment.patient_id')
    grievances = db.relationship('Grievance', back_populates='user', lazy='dynamic')
    referrals = db.relationship('Referral', back_populates='patient', lazy='dynamic')
    visits = db.relationship('Visit', back_populates='patient', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'


# ---------------------------
# ADMIN
# ---------------------------
class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # hashed
    role = db.Column(db.String(50), default='admin')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    admin_logs = db.relationship('AdminLog', back_populates='admin', lazy='dynamic')
    hospitals_updated = db.relationship('Hospital', back_populates='updated_by', lazy='dynamic')

    def __repr__(self):
        return f'<Admin {self.username}>'


class AdminLog(db.Model):
    __tablename__ = 'admin_logs'
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    admin = db.relationship('Admin', back_populates='admin_logs')
    user = db.relationship('Users', back_populates='admin_logs')


# ---------------------------
# HOSPITAL & HOSPITAL_INFO
# ---------------------------
class Hospital_info(db.Model):
    __tablename__ = 'hospital_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    name = db.Column(db.String(150), nullable=False)
    type = db.Column(db.String(300), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    is_multi_level = db.Column(db.Boolean, default=False)  # whether hospital has multiple floors
    reg_id = db.Column(db.String(200), nullable=False, unique=True)
    availability = db.Column(db.String(150), nullable=True)
    role = db.Column(db.String(10), default='hospital', nullable=False)

    # One-to-one with Hospital
    hospital = db.relationship('Hospital', back_populates='hospital_info', uselist=False, single_parent=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<HospitalInfo {self.name}>'


class Hospital(db.Model):
    __tablename__ = 'hospital'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(500), nullable=True)
    contact_num = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(150), nullable=True)
    hospital_type = db.Column(db.String(100), nullable=True)
    bedAvailability = db.Column(db.Integer, nullable=True, default=0)
    oxygenUnits = db.Column(db.Integer, nullable=True, default=0)
    opd_status = db.Column(db.Enum(OPDStatus), default=OPDStatus.OPEN, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    lastupdatedBy = db.Column(db.Integer, db.ForeignKey('admin.id'), nullable=True)

    hospital_info_id = db.Column(db.Integer, db.ForeignKey('hospital_info.id'), unique=True, nullable=True)
    hospital_info = db.relationship('Hospital_info', back_populates='hospital')

    # relationships
    updated_by = db.relationship('Admin', back_populates='hospitals_updated')
    inventories = db.relationship('InventoryItem', back_populates='hospital', lazy='dynamic', cascade='all, delete-orphan')
    floors = db.relationship('Floor', back_populates='hospital', lazy='dynamic', cascade='all, delete-orphan')
    doctors = db.relationship('Doctors_Info', secondary=hospital_doctor, back_populates='hospitals', lazy='dynamic')
    bloodbanks = db.relationship('BloodBank', secondary=bloodbank_hospital, back_populates='hospitals', lazy='dynamic')
    opds = db.relationship('OPD', back_populates='hospital', lazy='dynamic', cascade='all, delete-orphan')
    ambulances = db.relationship('Ambulance', back_populates='hospital', lazy='dynamic', cascade='all, delete-orphan')
    emergencies = db.relationship('Emergency', back_populates='hospital', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Hospital {self.name}>'


# ---------------------------
# FLOOR / WARD CATEGORY / WARD / BED
# ---------------------------
class Floor(db.Model):
    __tablename__ = 'floor'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    floor_number = db.Column(db.String(50), nullable=False)  # allow "G", "0", "1", "Basement"
    floor_name = db.Column(db.String(100), nullable=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id', ondelete="CASCADE"), nullable=False)

    hospital = db.relationship('Hospital', back_populates='floors')
    wards = db.relationship('Ward', back_populates='floor', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('hospital_id', 'floor_number', name='uq_hospital_floor_number'),
    )

    def __repr__(self):
        return f'<Floor {self.floor_number} of Hospital {self.hospital_id}>'


class WardCategory(db.Model):
    __tablename__ = 'ward_category'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # ICU, General, Maternity, etc.
    description = db.Column(db.Text, nullable=True)

    wards = db.relationship('Ward', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f'<WardCategory {self.name}>'


class Ward(db.Model):
    __tablename__ = 'ward'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ward_number = db.Column(db.String(50), nullable=False)  # unique per floor
    category_id = db.Column(db.Integer, db.ForeignKey('ward_category.id', ondelete="SET NULL"), nullable=True)
    capacity = db.Column(db.Integer, nullable=False, default=0)
    floor_id = db.Column(db.Integer, db.ForeignKey('floor.id', ondelete="CASCADE"), nullable=False)

    floor = db.relationship('Floor', back_populates='wards')
    category = db.relationship('WardCategory', back_populates='wards')
    beds = db.relationship('Bed', back_populates='ward', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (
        UniqueConstraint('floor_id', 'ward_number', name='uq_floor_ward_number'),
    )

    def __repr__(self):
        return f'<Ward {self.ward_number} on Floor {self.floor_id}>'


class Bed(db.Model):
    __tablename__ = 'bed'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ward_id = db.Column(db.Integer, db.ForeignKey('ward.id', ondelete="CASCADE"), nullable=False)
    bed_number = db.Column(db.String(50), nullable=False)  # "A1", "B2", etc.
    status = db.Column(db.Enum(BedStatus), nullable=False, default=BedStatus.VACANT)
    bed_type = db.Column(db.String(100), nullable=True)  # General, ICU, Ventilator, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ward = db.relationship('Ward', back_populates='beds')

    __table_args__ = (
        UniqueConstraint('ward_id', 'bed_number', name='uq_ward_bed_number'),
    )

    def __repr__(self):
        return f'<Bed {self.bed_number} ({self.status}) in Ward {self.ward_id}>'


# ---------------------------
# DOCTORS, SCHEDULES, OPD, SLOTS, RESERVATIONS, APPOINTMENTS
# ---------------------------
class Doctors_Info(db.Model):
    __tablename__ = 'doctors_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    specialisation = db.Column(db.String(200), nullable=True)
    availability = db.Column(db.String(200), nullable=True)
    mail = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(50), nullable=True)

    hospitals = db.relationship('Hospital', secondary=hospital_doctor, back_populates='doctors', lazy='dynamic')
    schedules = db.relationship('DoctorSchedule', back_populates='doctor', lazy='dynamic', cascade='all, delete-orphan')
    visits = db.relationship('Visit', back_populates='doctor', lazy='dynamic')
    prescriptions = db.relationship('Prescription', back_populates='doctor', lazy='dynamic')

    def __repr__(self):
        return f'<Doctor {self.name} - {self.specialisation}>'


class DoctorSchedule(db.Model):
    __tablename__ = 'doctor_schedule'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors_info.id', ondelete="CASCADE"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id', ondelete="CASCADE"), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=True)  # 0=Mon .. 6=Sun
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    specific_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.String(500), nullable=True)

    doctor = db.relationship('Doctors_Info', back_populates='schedules')
    hospital = db.relationship('Hospital')

    def __repr__(self):
        return f'<DoctorSchedule doc={self.doctor_id} hosp={self.hospital_id}>'


class OPD(db.Model):
    __tablename__ = 'opd'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id', ondelete="CASCADE"), nullable=False)
    department = db.Column(db.String(150), nullable=False)
    shift = db.Column(db.String(80), nullable=True)
    from_timing = db.Column(db.Time, nullable=True)
    to_timing = db.Column(db.Time, nullable=True)
    from_day = db.Column(db.String(20), nullable=True)
    to_day = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=True)

    hospital = db.relationship('Hospital', back_populates='opds')
    slots = db.relationship('opdSlots', back_populates='opd', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<OPD {self.department} @ Hospital {self.hospital_id}>'


class opdSlots(db.Model):
    __tablename__ = 'opd_slots'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    opd_id = db.Column(db.Integer, db.ForeignKey('opd.id', ondelete="CASCADE"), nullable=False)
    opd_slot_id = db.Column(db.String(50), nullable=False, unique=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors_info.id', ondelete="SET NULL"), nullable=True)
    slot_start = db.Column(db.DateTime, nullable=False)
    slot_end = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=1)
    occupancy = db.Column(db.Integer, nullable=False, default=0)

    opd = db.relationship('OPD', back_populates='slots')
    doctor = db.relationship('Doctors_Info')
    reservations = db.relationship('OPDSlotReservation', back_populates='slot', lazy='dynamic', cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', back_populates='slot', lazy='dynamic')

    def __repr__(self):
        return f'<opdSlots {self.opd_slot_id} ({self.slot_start} - {self.slot_end})>'


class OPDSlotReservation(db.Model):
    __tablename__ = 'opd_slot_reservation'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('opd_slots.id', ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="SET NULL"), nullable=True)
    occupied_time = db.Column(db.Integer, nullable=True)  # in minutes
    reason = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    slot = db.relationship('opdSlots', back_populates='reservations')
    user = db.relationship('Users', back_populates='opd_reservations')

    def __repr__(self):
        return f'<OPDSlotReservation slot={self.slot_id} user={self.user_id}>'


class Appointment(db.Model):
    __tablename__ = 'appointment'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    appointment_type = db.Column(db.String(50), nullable=False)  # 'opd', 'ambulance', 'blood', etc.
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id', ondelete="CASCADE"), nullable=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors_info.id', ondelete="SET NULL"), nullable=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('opd_slots.id', ondelete="SET NULL"), nullable=True)
    booked_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="SET NULL"), nullable=True)
    status = db.Column(db.Enum(AppointmentStatus), default=AppointmentStatus.PENDING, nullable=False)
    scheduled_time = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reason = db.Column(db.String(500), nullable=True)

    patient = db.relationship('Users', back_populates='appointments', foreign_keys=[patient_id])
    booked_by_user = db.relationship('Users', foreign_keys=[booked_by_user_id])
    hospital = db.relationship('Hospital')
    doctor = db.relationship('Doctors_Info')
    slot = db.relationship('opdSlots', back_populates='appointments')

    def __repr__(self):
        return f'<Appointment {self.id} type={self.appointment_type} patient={self.patient_id}>'


class Visit(db.Model):
    __tablename__ = 'visit'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id', ondelete="SET NULL"), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors_info.id', ondelete="SET NULL"), nullable=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id', ondelete="SET NULL"), nullable=True)
    visit_time = db.Column(db.DateTime, default=datetime.utcnow)
    clinical_notes = db.Column(JSON, nullable=True)
    finalized = db.Column(db.Boolean, default=False)

    appointment = db.relationship('Appointment')
    patient = db.relationship('Users', back_populates='visits')
    doctor = db.relationship('Doctors_Info', back_populates='visits')
    prescriptions = db.relationship('Prescription', back_populates='visit', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Visit patient={self.patient_id} doctor={self.doctor_id}>'


class Prescription(db.Model):
    __tablename__ = 'prescription'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    visit_id = db.Column(db.Integer, db.ForeignKey('visit.id', ondelete="CASCADE"), nullable=False)
    prescribed_by = db.Column(db.Integer, db.ForeignKey('doctors_info.id', ondelete="SET NULL"), nullable=True)
    items = db.Column(JSON, nullable=False)  # array of med objects {name, dose, freq, duration}
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    visit = db.relationship('Visit', back_populates='prescriptions')
    doctor = db.relationship('Doctors_Info', back_populates='prescriptions')

    def __repr__(self):
        return f'<Prescription {self.id} for visit {self.visit_id}>'


# ---------------------------
# BLOOD BANK / INVENTORY
# ---------------------------
class BloodBank(db.Model):
    __tablename__ = 'blood_bank'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(500), nullable=False)
    contact_no = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    blood_types_available = db.Column(JSON, nullable=True)
    stock_levels = db.Column(JSON, nullable=True)
    category = db.Column(db.String(80), nullable=True)
    role = db.Column(db.String(10), nullable=False, default='bloodbank')
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow)

    hospitals = db.relationship('Hospital', secondary=bloodbank_hospital, back_populates='bloodbanks', lazy='dynamic')
    inventories = db.relationship('BloodInventory', back_populates='bloodbank', lazy='dynamic', cascade='all, delete-orphan')
    reservations = db.relationship('ReserveBlood', back_populates='bloodbank', lazy='dynamic')

    def __repr__(self):
        return f'<BloodBank {self.name}>'


class BloodInventory(db.Model):
    __tablename__ = 'blood_inventory'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bloodbank_id = db.Column(db.Integer, db.ForeignKey('blood_bank.id', ondelete="CASCADE"), nullable=False)
    blood_type = db.Column(db.String(10), nullable=False)
    units = db.Column(db.Integer, nullable=False, default=0)
    expiry_date = db.Column(db.Date, nullable=True)
    lot_number = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bloodbank = db.relationship('BloodBank', back_populates='inventories')
    reservations = db.relationship('ReserveBlood', back_populates='blood_inventory', lazy='dynamic')

    __table_args__ = (
        UniqueConstraint('bloodbank_id', 'blood_type', 'lot_number', name='uq_bloodbank_type_lot'),
    )

    def __repr__(self):
        return f'<BloodInventory {self.blood_type} units={self.units}>'


class ReserveBlood(db.Model):
    __tablename__ = 'reserve_blood'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('Users', back_populates='blood_requests')

    requester_name = db.Column(db.String(150), nullable=True, default="none")
    requester_phone = db.Column(db.String(30), nullable=True, default="none")
    requester_email = db.Column(db.String(150), nullable=True, default="none")

    blood_group = db.Column(db.String(10), nullable=False)
    quantity_units = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(500), nullable=False)
    reference = db.Column(db.String(200), nullable=False)

    bloodbank_id = db.Column(db.Integer, db.ForeignKey('blood_bank.id'), nullable=True)
    bloodbank = db.relationship('BloodBank', back_populates='reservations')

    blood_inventory_id = db.Column(db.Integer, db.ForeignKey('blood_inventory.id'), nullable=True)
    blood_inventory = db.relationship('BloodInventory', back_populates='reservations')

    status = db.Column(db.Enum(StatusEnum), default=StatusEnum.PENDING, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ReserveBlood {self.id} blood_group={self.blood_group}>'


# Generic live tracking for ambulances or shipments
class LiveTracking(db.Model):
    __tablename__ = 'live_tracking'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    resource_type = db.Column(db.String(50), nullable=False)  # ambulance, blood_shipment
    resource_id = db.Column(db.Integer, nullable=False)  # polymorphic reference id
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<LiveTracking {self.resource_type} id={self.resource_id} @ {self.timestamp}>'


# ---------------------------
# SUPPLIER & INVENTORY
# ---------------------------
class Supplier(db.Model):
    __tablename__ = 'supplier'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    contact_email = db.Column(db.String(150))
    phone = db.Column(db.String(50))
    performance_score = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)

    items = db.relationship('InventoryItem', back_populates='supplier', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Supplier {self.name}>'


class InventoryItem(db.Model):
    __tablename__ = 'inventory_item'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id'), nullable=False)
    drug_name = db.Column(db.String(150), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    expiry_time = db.Column(db.Date, nullable=True)
    min_threshold = db.Column(db.Integer, nullable=False, default=0)
    buffer_stock = db.Column(db.Integer, nullable=False, default=0)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hospital = db.relationship('Hospital', back_populates='inventories')
    supplier = db.relationship('Supplier', back_populates='items')

    def __repr__(self):
        return f'<InventoryItem {self.drug_name} qty={self.quantity}>'


# ---------------------------
# AMBULANCE, FORWARD REQUEST, GRIEVANCE, REFERRAL, NOTIFICATION
# ---------------------------
class Ambulance(db.Model):
    __tablename__ = 'ambulance'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id', ondelete="CASCADE"), nullable=True)
    type = db.Column(db.Enum(AmbulanceType), nullable=False, default=AmbulanceType.PUBLIC)
    status = db.Column(db.Enum(AmbulanceStatus), nullable=False, default=AmbulanceStatus.VACANT)
    driver_name = db.Column(db.String(150), nullable=True)
    driver_phone = db.Column(db.String(50), nullable=True)
    current_lat = db.Column(db.Float, nullable=True)
    current_lng = db.Column(db.Float, nullable=True)
    last_reported = db.Column(db.DateTime, default=datetime.utcnow)

    hospital = db.relationship('Hospital', back_populates='ambulances')

    def __repr__(self):
        return f'<Ambulance {self.id} status={self.status}>'


class ForwardedRequest(db.Model):
    __tablename__ = 'forwarded_request'
    id = db.Column(db.Integer, primary_key=True)
    emergency_id = db.Column(db.Integer, db.ForeignKey('emergency.id', ondelete='CASCADE'), nullable=True)
    forwarded_to = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    emergency = db.relationship('Emergency', back_populates='forwards')

    def __repr__(self):
        return f'<ForwardedRequest {self.id} to={self.forwarded_to}>'


class Grievance(db.Model):
    __tablename__ = 'grievance'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    category = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('Users', back_populates='grievances')

    def __repr__(self):
        return f'<Grievance {self.id} user={self.user_id}>'


class Referral(db.Model):
    __tablename__ = 'referral'
    id = db.Column(db.Integer, primary_key=True)
    from_hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id', ondelete='SET NULL'), nullable=True)
    to_hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id', ondelete='SET NULL'), nullable=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reason = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    from_hospital = db.relationship('Hospital', foreign_keys=[from_hospital_id])
    to_hospital = db.relationship('Hospital', foreign_keys=[to_hospital_id])
    patient = db.relationship('Users', back_populates='referrals')

    def __repr__(self):
        return f'<Referral {self.id} patient={self.patient_id}>'


class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    title = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    meta_info = db.Column(JSON, nullable=True)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('Users')

    def __repr__(self):
        return f'<Notification {self.id} to={self.user_id}>'


# ---------------------------
# EMERGENCY
# ---------------------------
class Emergency(db.Model):
    __tablename__ = 'emergency'
    id = db.Column(db.Integer, primary_key=True)
    emergency_type = db.Column(db.String(100), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospital.id', ondelete='SET NULL'), nullable=True)
    location = db.Column(db.String(500), nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    details = db.Column(db.Text, nullable=True)
    image_filename = db.Column(db.String(200), nullable=True)
    audio_filename = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_ip = db.Column(db.String(100), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user = db.relationship('Users', back_populates='emergencies')

    forwarded_to_org = db.Column(db.String(200), nullable=True)
    forward_status = db.Column(db.String(100), default='Pending')

    hospital = db.relationship('Hospital', back_populates='emergencies')
    forwards = db.relationship('ForwardedRequest', back_populates='emergency', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Emergency {self.id} type={self.emergency_type}>'


# ---------------------------
# DB-level Guard: single-floor enforcement
# ---------------------------
@event.listens_for(Floor, "before_insert")
def enforce_single_level_before_insert(mapper, connection, target):
    """
    Enforce rule: if the associated hospital's hospital_info.is_multi_level is False,
    only one Floor must exist (and its floor_number should be '0' or 'G').
    This uses raw SQL via the connection to avoid requiring a session.
    """
    if not target.hospital_id:
        return

    # count existing floors for that hospital
    existing = connection.execute(
        text("SELECT COUNT(1) FROM floor WHERE hospital_id = :hid"),
        {"hid": target.hospital_id}
    ).scalar()

    # get is_multi_level from hospital_info if available
    is_multi = connection.execute(
        text("""
            SELECT hi.is_multi_level
            FROM hospital_info hi
            JOIN hospital h ON hi.id = h.hospital_info_id
            WHERE h.id = :hid
        """),
        {"hid": target.hospital_id}
    ).scalar()

    # If is_multi is known and False => enforce single-floor constraints
    if is_multi is not None and is_multi is False:
        if existing and existing > 0:
            raise ValueError("Single-level hospital can only have one Floor (use floor_number = '0').")
        # allow some leniency for 'G' or '0' but we enforce '0' here
        if str(target.floor_number) != '0':
            raise ValueError("For single-level hospitals, floor_number must be '0'.")

# End of models.py
