#!/usr/bin/env python3
"""
Debug appointment slots endpoint
"""
import sys
from app import create_app, db
from app.models import Hospital, opdSlots, OPD, Doctors_Info

# Create Flask application
app = create_app()

def debug_appointment_data():
    """Debug appointment slot data"""
    with app.app_context():
        print("=== Debugging Appointment Slots ===")
        
        # Check hospitals
        hospitals = Hospital.query.all()
        print(f"Total hospitals: {len(hospitals)}")
        for hospital in hospitals:
            print(f"  - {hospital.name} (ID: {hospital.id})")
        
        # Check OPDs
        opds = OPD.query.all() 
        print(f"Total OPDs: {len(opds)}")
        for opd in opds:
            print(f"  - {opd.department} at Hospital {opd.hospital_id} (ID: {opd.id})")
        
        # Check doctors
        doctors = Doctors_Info.query.all()
        print(f"Total doctors: {len(doctors)}")
        for doctor in doctors:
            print(f"  - {doctor.name} (ID: {doctor.id})")
        
        # Check slots
        slots = opdSlots.query.all()
        print(f"Total slots: {len(slots)}")
        
        # Check specific query from appointment endpoint
        print("\n=== Testing Query from Appointment Endpoint ===")
        try:
            query = opdSlots.query.join(OPD).filter(OPD.hospital_id == 1)
            print(f"Slots for hospital 1: {query.count()}")
            
            # Test the full query
            from datetime import datetime
            full_query = query.filter(
                opdSlots.slot_start > datetime.utcnow(),
                opdSlots.occupancy < opdSlots.capacity
            ).order_by(opdSlots.slot_start.asc())
            
            available_slots = full_query.limit(5).all()
            print(f"Available future slots (first 5): {len(available_slots)}")
            
            for slot in available_slots:
                print(f"  - Slot {slot.opd_slot_id}: {slot.slot_start} (capacity: {slot.capacity}, occupancy: {slot.occupancy})")
                if slot.doctor:
                    print(f"    Doctor: {slot.doctor.name}")
                if slot.opd:
                    print(f"    OPD: {slot.opd.department}")
                    
        except Exception as e:
            print(f"Error in query: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    debug_appointment_data()