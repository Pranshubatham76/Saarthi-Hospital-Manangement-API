#!/usr/bin/env python3
"""
Create test data for the hospital management system
"""
import os
from datetime import datetime, timedelta
from app import create_app, db
from app.models import Hospital, Doctors_Info, OPD, opdSlots

# Create Flask application
app = create_app()

def create_test_data():
    """Create test data for appointments"""
    with app.app_context():
        print("Creating test data for appointments...")
        
        # Get or create a hospital
        hospital = Hospital.query.first()
        if not hospital:
            print("No hospitals found in database")
            return
            
        print(f"Using hospital: {hospital.name} (ID: {hospital.id})")
        
        # Create a test doctor
        doctor = Doctors_Info.query.first()
        if not doctor:
            print("Creating test doctor...")
            doctor = Doctors_Info(
                name="Dr. John Smith",
                email="drjohn@example.com",
                phone_num="555-1234",
                specialization="General Medicine",
                hospital_id=hospital.id
            )
            db.session.add(doctor)
            db.session.commit()
            
        print(f"Using doctor: {doctor.name} (ID: {doctor.id})")
        
        # Create OPD
        opd = OPD.query.filter_by(hospital_id=hospital.id).first()
        if not opd:
            print("Creating OPD...")
            opd = OPD(
                hospital_id=hospital.id,
                department="General Medicine",
                fees=500.0,
                timing="9:00 AM - 5:00 PM"
            )
            db.session.add(opd)
            db.session.commit()
            
        print(f"Using OPD: {opd.department} (ID: {opd.id})")
        
        # Create OPD slots for next 7 days
        print("Creating OPD slots...")
        slots_created = 0
        
        for day in range(1, 8):  # Next 7 days
            date = datetime.now() + timedelta(days=day)
            
            # Create morning slots (9 AM to 12 PM)
            for hour in range(9, 12):
                slot_time = date.replace(hour=hour, minute=0, second=0, microsecond=0)
                
                # Check if slot already exists
                existing_slot = opdSlots.query.filter_by(
                    opd_id=opd.id,
                    doctor_id=doctor.id,
                    slot_start=slot_time
                ).first()
                
                if not existing_slot:
                    slot_id = f"OPD_{opd.id}_DR_{doctor.id}_{slot_time.strftime('%Y%m%d_%H%M')}"
                    slot = opdSlots(
                        opd_id=opd.id,
                        opd_slot_id=slot_id,
                        doctor_id=doctor.id,
                        slot_start=slot_time,
                        slot_end=slot_time + timedelta(hours=1),
                        capacity=10,
                        occupancy=0
                    )
                    db.session.add(slot)
                    slots_created += 1
        
        db.session.commit()
        print(f"Created {slots_created} OPD slots")
        
        # Display summary
        total_slots = opdSlots.query.count()
        available_slots = opdSlots.query.filter(
            opdSlots.slot_start > datetime.now(),
            opdSlots.occupancy < opdSlots.capacity
        ).count()
        
        print(f"Total slots in database: {total_slots}")
        print(f"Available future slots: {available_slots}")
        
        print("Test data creation completed!")

if __name__ == '__main__':
    create_test_data()