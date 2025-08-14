#!/usr/bin/env python3
"""
Database Initialization Script for Hospital Management System
This script creates all database tables and populates them with sample data.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    from app.models import db, *
    from app.utils.helpers import hash_password
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all required packages are installed:")
    print("pip install Flask Flask-SQLAlchemy python-dotenv bcrypt")
    sys.exit(1)

def create_sample_data():
    """Create sample data for development and testing"""
    
    print("Creating sample data...")
    
    # Create default admin user
    admin = Admin(
        username='admin',
        password=hash_password('admin123'),
        role='admin'
    )
    db.session.add(admin)
    
    # Create ward categories
    ward_categories = [
        WardCategory(name='General', description='General ward for regular patients'),
        WardCategory(name='ICU', description='Intensive Care Unit'),
        WardCategory(name='CCU', description='Cardiac Care Unit'),
        WardCategory(name='Maternity', description='Maternity ward'),
        WardCategory(name='Pediatric', description='Children\'s ward'),
        WardCategory(name='Emergency', description='Emergency department beds'),
        WardCategory(name='Surgery', description='Post-surgical recovery beds')
    ]
    
    for category in ward_categories:
        db.session.add(category)
    
    # Create sample users
    sample_users = [
        Users(
            username='john_doe',
            fullname='John Doe',
            email='john@example.com',
            password=hash_password('password123'),
            phone_num='+1234567890',
            location='New York, NY',
            role='user'
        ),
        Users(
            username='jane_smith',
            fullname='Jane Smith',
            email='jane@example.com',
            password=hash_password('password123'),
            phone_num='+1234567891',
            location='Los Angeles, CA',
            role='user'
        ),
        Users(
            username='dr_wilson',
            fullname='Dr. Robert Wilson',
            email='wilson@hospital.com',
            password=hash_password('password123'),
            phone_num='+1234567892',
            location='Chicago, IL',
            role='doctor'
        )
    ]
    
    for user in sample_users:
        db.session.add(user)
    
    # Create sample hospital info
    sample_hospital_info = [
        Hospital_info(
            username='city_general',
            name='City General Hospital',
            type='General',
            email='info@citygeneral.com',
            password=hash_password('hospital123'),
            location='123 Main Street, New York, NY 10001',
            is_multi_level=True,
            reg_id='HOSP20240001',
            availability='24/7',
            role='hospital'
        ),
        Hospital_info(
            username='metro_medical',
            name='Metro Medical Center',
            type='Specialized',
            email='info@metropmedical.com',
            password=hash_password('hospital123'),
            location='456 Health Ave, Los Angeles, CA 90001',
            is_multi_level=True,
            reg_id='HOSP20240002',
            availability='24/7',
            role='hospital'
        ),
        Hospital_info(
            username='community_clinic',
            name='Community Clinic',
            type='Clinic',
            email='info@communityclinic.com',
            password=hash_password('hospital123'),
            location='789 Care Street, Chicago, IL 60601',
            is_multi_level=False,
            reg_id='HOSP20240003',
            availability='8AM-6PM',
            role='hospital'
        )
    ]
    
    for hospital_info in sample_hospital_info:
        db.session.add(hospital_info)
    
    # Commit hospital info first to get IDs
    db.session.commit()
    
    # Create sample hospitals
    sample_hospitals = [
        Hospital(
            name='City General Hospital',
            location='123 Main Street, New York, NY 10001',
            contact_num='+1-555-0101',
            email='info@citygeneral.com',
            hospital_type='Government',
            bedAvailability=150,
            oxygenUnits=50,
            opd_status=OPDStatus.OPEN,
            hospital_info_id=sample_hospital_info[0].id
        ),
        Hospital(
            name='Metro Medical Center',
            location='456 Health Ave, Los Angeles, CA 90001',
            contact_num='+1-555-0102',
            email='info@metropmedical.com',
            hospital_type='Private',
            bedAvailability=200,
            oxygenUnits=75,
            opd_status=OPDStatus.OPEN,
            hospital_info_id=sample_hospital_info[1].id
        ),
        Hospital(
            name='Community Clinic',
            location='789 Care Street, Chicago, IL 60601',
            contact_num='+1-555-0103',
            email='info@communityclinic.com',
            hospital_type='Private',
            bedAvailability=50,
            oxygenUnits=20,
            opd_status=OPDStatus.LIMITED,
            hospital_info_id=sample_hospital_info[2].id
        )
    ]
    
    for hospital in sample_hospitals:
        db.session.add(hospital)
    
    # Commit hospitals to get IDs
    db.session.commit()
    
    # Create sample doctors
    sample_doctors = [
        Doctors_Info(
            name='Dr. Sarah Johnson',
            specialisation='Cardiology',
            availability='Mon-Fri 9AM-5PM',
            mail='sarah.johnson@citygeneral.com',
            phone='+1-555-0201'
        ),
        Doctors_Info(
            name='Dr. Michael Brown',
            specialisation='Pediatrics',
            availability='Mon-Sat 8AM-4PM',
            mail='michael.brown@metropmedical.com',
            phone='+1-555-0202'
        ),
        Doctors_Info(
            name='Dr. Emily Davis',
            specialisation='General Medicine',
            availability='Tue-Thu 10AM-6PM',
            mail='emily.davis@communityclinic.com',
            phone='+1-555-0203'
        ),
        Doctors_Info(
            name='Dr. David Wilson',
            specialisation='Orthopedics',
            availability='Mon-Fri 8AM-3PM',
            mail='david.wilson@citygeneral.com',
            phone='+1-555-0204'
        )
    ]
    
    for doctor in sample_doctors:
        db.session.add(doctor)
    
    # Commit doctors to get IDs
    db.session.commit()
    
    # Associate doctors with hospitals (many-to-many)
    sample_hospitals[0].doctors.append(sample_doctors[0])  # Dr. Johnson -> City General
    sample_hospitals[0].doctors.append(sample_doctors[3])  # Dr. Wilson -> City General
    sample_hospitals[1].doctors.append(sample_doctors[1])  # Dr. Brown -> Metro Medical
    sample_hospitals[2].doctors.append(sample_doctors[2])  # Dr. Davis -> Community Clinic
    
    # Create floors for multi-level hospitals
    floors_data = [
        # City General Hospital floors
        Floor(hospital_id=sample_hospitals[0].id, floor_number='G', floor_name='Ground Floor'),
        Floor(hospital_id=sample_hospitals[0].id, floor_number='1', floor_name='First Floor'),
        Floor(hospital_id=sample_hospitals[0].id, floor_number='2', floor_name='Second Floor'),
        
        # Metro Medical Center floors
        Floor(hospital_id=sample_hospitals[1].id, floor_number='G', floor_name='Ground Floor'),
        Floor(hospital_id=sample_hospitals[1].id, floor_number='1', floor_name='First Floor'),
        Floor(hospital_id=sample_hospitals[1].id, floor_number='2', floor_name='Second Floor'),
        Floor(hospital_id=sample_hospitals[1].id, floor_number='3', floor_name='Third Floor'),
        
        # Community Clinic (single floor)
        Floor(hospital_id=sample_hospitals[2].id, floor_number='0', floor_name='Main Floor')
    ]
    
    for floor in floors_data:
        db.session.add(floor)
    
    # Commit floors to get IDs
    db.session.commit()
    
    # Create wards
    wards_data = [
        # City General Hospital wards
        Ward(floor_id=floors_data[0].id, ward_number='G01', category_id=ward_categories[5].id, capacity=20),  # Emergency
        Ward(floor_id=floors_data[1].id, ward_number='101', category_id=ward_categories[0].id, capacity=30),  # General
        Ward(floor_id=floors_data[1].id, ward_number='102', category_id=ward_categories[1].id, capacity=15),  # ICU
        Ward(floor_id=floors_data[2].id, ward_number='201', category_id=ward_categories[3].id, capacity=25),  # Maternity
        
        # Metro Medical Center wards
        Ward(floor_id=floors_data[3].id, ward_number='G01', category_id=ward_categories[5].id, capacity=15),  # Emergency
        Ward(floor_id=floors_data[4].id, ward_number='101', category_id=ward_categories[4].id, capacity=20),  # Pediatric
        Ward(floor_id=floors_data[5].id, ward_number='201', category_id=ward_categories[1].id, capacity=20),  # ICU
        Ward(floor_id=floors_data[6].id, ward_number='301', category_id=ward_categories[6].id, capacity=25),  # Surgery
        
        # Community Clinic wards
        Ward(floor_id=floors_data[7].id, ward_number='001', category_id=ward_categories[0].id, capacity=15),  # General
    ]
    
    for ward in wards_data:
        db.session.add(ward)
    
    # Commit wards to get IDs
    db.session.commit()
    
    # Create beds
    bed_statuses = [BedStatus.VACANT, BedStatus.OCCUPIED, BedStatus.RESERVED]
    for ward in wards_data:
        for bed_num in range(1, ward.capacity + 1):
            bed = Bed(
                ward_id=ward.id,
                bed_number=f"{ward.ward_number}-{bed_num:02d}",
                status=bed_statuses[bed_num % len(bed_statuses)],
                bed_type=ward.category.name if ward.category else 'General'
            )
            db.session.add(bed)
    
    # Create OPDs
    opds_data = [
        OPD(
            hospital_id=sample_hospitals[0].id,
            department='Cardiology',
            shift='Morning',
            from_timing=datetime.strptime('09:00', '%H:%M').time(),
            to_timing=datetime.strptime('13:00', '%H:%M').time(),
            from_day='Monday',
            to_day='Friday',
            description='Cardiac care and consultation'
        ),
        OPD(
            hospital_id=sample_hospitals[1].id,
            department='Pediatrics',
            shift='All Day',
            from_timing=datetime.strptime('08:00', '%H:%M').time(),
            to_timing=datetime.strptime('16:00', '%H:%M').time(),
            from_day='Monday',
            to_day='Saturday',
            description='Children\'s healthcare'
        ),
        OPD(
            hospital_id=sample_hospitals[2].id,
            department='General Medicine',
            shift='Afternoon',
            from_timing=datetime.strptime('14:00', '%H:%M').time(),
            to_timing=datetime.strptime('18:00', '%H:%M').time(),
            from_day='Tuesday',
            to_day='Thursday',
            description='General medical consultation'
        )
    ]
    
    for opd in opds_data:
        db.session.add(opd)
    
    # Commit OPDs to get IDs
    db.session.commit()
    
    # Create OPD slots for the next 7 days
    for opd in opds_data:
        for day_offset in range(7):
            slot_date = datetime.now() + timedelta(days=day_offset)
            
            # Create slots every 30 minutes during OPD hours
            current_time = datetime.combine(slot_date.date(), opd.from_timing)
            end_time = datetime.combine(slot_date.date(), opd.to_timing)
            
            slot_counter = 1
            while current_time < end_time:
                slot_end = current_time + timedelta(minutes=30)
                
                opd_slot = opdSlots(
                    opd_id=opd.id,
                    opd_slot_id=f"{opd.department[:3].upper()}{slot_date.strftime('%Y%m%d')}{slot_counter:03d}",
                    doctor_id=sample_doctors[0].id if opd.department == 'Cardiology' else 
                              sample_doctors[1].id if opd.department == 'Pediatrics' else 
                              sample_doctors[2].id,
                    slot_start=current_time,
                    slot_end=slot_end,
                    capacity=3,
                    occupancy=0
                )
                db.session.add(opd_slot)
                
                current_time = slot_end
                slot_counter += 1
    
    # Create sample blood banks
    blood_banks = [
        BloodBank(
            name='Central Blood Bank',
            location='100 Blood Drive, New York, NY 10001',
            contact_no='+1-555-0301',
            email='info@centralbloodbank.org',
            blood_types_available=['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
            stock_levels={'A+': 50, 'A-': 30, 'B+': 40, 'B-': 25, 'AB+': 20, 'AB-': 15, 'O+': 60, 'O-': 45},
            category='Government'
        ),
        BloodBank(
            name='Metro Blood Services',
            location='200 Donation Ave, Los Angeles, CA 90001',
            contact_no='+1-555-0302',
            email='contact@metroblood.org',
            blood_types_available=['A+', 'B+', 'AB+', 'O+', 'O-'],
            stock_levels={'A+': 35, 'B+': 30, 'AB+': 15, 'O+': 40, 'O-': 25},
            category='Private'
        )
    ]
    
    for blood_bank in blood_banks:
        db.session.add(blood_bank)
    
    # Commit blood banks to get IDs
    db.session.commit()
    
    # Create blood inventory
    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    for blood_bank in blood_banks:
        for blood_type in blood_types:
            if blood_type in blood_bank.blood_types_available:
                inventory = BloodInventory(
                    bloodbank_id=blood_bank.id,
                    blood_type=blood_type,
                    units=blood_bank.stock_levels.get(blood_type, 0),
                    expiry_date=(datetime.now() + timedelta(days=30)).date(),
                    lot_number=f"LOT{blood_bank.id}{blood_type.replace('+', 'P').replace('-', 'N')}{datetime.now().strftime('%Y%m')}"
                )
                db.session.add(inventory)
    
    # Associate blood banks with hospitals
    blood_banks[0].hospitals.append(sample_hospitals[0])
    blood_banks[0].hospitals.append(sample_hospitals[2])
    blood_banks[1].hospitals.append(sample_hospitals[1])
    
    # Create sample ambulances
    ambulances = [
        Ambulance(
            hospital_id=sample_hospitals[0].id,
            type=AmbulanceType.PUBLIC,
            status=AmbulanceStatus.VACANT,
            driver_name='John Driver',
            driver_phone='+1-555-0401'
        ),
        Ambulance(
            hospital_id=sample_hospitals[1].id,
            type=AmbulanceType.PRIVATE,
            status=AmbulanceStatus.VACANT,
            driver_name='Mike Transport',
            driver_phone='+1-555-0402'
        ),
        Ambulance(
            hospital_id=sample_hospitals[0].id,
            type=AmbulanceType.PUBLIC,
            status=AmbulanceStatus.OCCUPIED,
            driver_name='Sarah Emergency',
            driver_phone='+1-555-0403'
        )
    ]
    
    for ambulance in ambulances:
        db.session.add(ambulance)
    
    # Create sample suppliers
    suppliers = [
        Supplier(
            name='MedSupply Corp',
            contact_email='orders@medsupply.com',
            phone='+1-555-0501',
            performance_score=4.5,
            notes='Reliable pharmaceutical supplier'
        ),
        Supplier(
            name='HealthEquip Ltd',
            contact_email='sales@healthequip.com',
            phone='+1-555-0502',
            performance_score=4.2,
            notes='Medical equipment specialist'
        )
    ]
    
    for supplier in suppliers:
        db.session.add(supplier)
    
    # Commit suppliers to get IDs
    db.session.commit()
    
    # Create sample inventory items
    inventory_items = [
        InventoryItem(
            hospital_id=sample_hospitals[0].id,
            drug_name='Paracetamol 500mg',
            quantity=1000,
            expiry_time=(datetime.now() + timedelta(days=365)).date(),
            min_threshold=100,
            buffer_stock=50,
            supplier_id=suppliers[0].id
        ),
        InventoryItem(
            hospital_id=sample_hospitals[0].id,
            drug_name='Amoxicillin 250mg',
            quantity=500,
            expiry_time=(datetime.now() + timedelta(days=180)).date(),
            min_threshold=50,
            buffer_stock=25,
            supplier_id=suppliers[0].id
        ),
        InventoryItem(
            hospital_id=sample_hospitals[1].id,
            drug_name='Insulin (Vial)',
            quantity=200,
            expiry_time=(datetime.now() + timedelta(days=90)).date(),
            min_threshold=20,
            buffer_stock=10,
            supplier_id=suppliers[0].id
        )
    ]
    
    for item in inventory_items:
        db.session.add(item)
    
    print("Sample data created successfully!")

def main():
    """Main initialization function"""
    print("🏥 Hospital Management System - Database Initialization")
    print("=" * 60)
    
    # Create Flask application
    app = create_app()
    
    with app.app_context():
        try:
            print("Creating database tables...")
            
            # Drop all tables (use with caution in production!)
            db.drop_all()
            
            # Create all tables
            db.create_all()
            
            print("✅ Database tables created successfully!")
            
            # Create sample data
            create_sample_data()
            
            # Commit all changes
            db.session.commit()
            
            print("✅ Database initialized with sample data!")
            print("\n📊 Summary:")
            print(f"   👥 Users: {Users.query.count()}")
            print(f"   🏥 Hospitals: {Hospital.query.count()}")
            print(f"   👨‍⚕️ Doctors: {Doctors_Info.query.count()}")
            print(f"   🏢 Floors: {Floor.query.count()}")
            print(f"   🏠 Wards: {Ward.query.count()}")
            print(f"   🛏️ Beds: {Bed.query.count()}")
            print(f"   🩺 OPDs: {OPD.query.count()}")
            print(f"   📅 OPD Slots: {opdSlots.query.count()}")
            print(f"   🩸 Blood Banks: {BloodBank.query.count()}")
            print(f"   🚑 Ambulances: {Ambulance.query.count()}")
            print(f"   📦 Inventory Items: {InventoryItem.query.count()}")
            
            print("\n🔑 Default Credentials:")
            print("   Admin: username='admin', password='admin123'")
            print("   User: username='john_doe', password='password123'")
            print("   Hospital: username='city_general', password='hospital123'")
            
            print("\n🚀 You can now start the application with: python run.py")
            
        except Exception as e:
            print(f"❌ Error initializing database: {str(e)}")
            db.session.rollback()
            raise
        
        finally:
            db.session.close()

if __name__ == '__main__':
    main()
