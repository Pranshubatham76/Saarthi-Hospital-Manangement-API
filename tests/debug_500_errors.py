#!/usr/bin/env python3
"""
Debug 500 errors in emergency stats and blood inventory
"""
from app import create_app, db
from app.models import Emergency, BloodInventory

app = create_app()

def debug_emergency_stats():
    """Debug emergency stats issues"""
    with app.app_context():
        print("=== Debugging Emergency Stats ===")
        
        try:
            # Check if Emergency model exists and has data
            emergencies = Emergency.query.all()
            print(f"Total emergencies in DB: {len(emergencies)}")
            
            # Check the fields we're using in the stats
            for emergency in emergencies[:3]:
                print(f"Emergency {emergency.id}:")
                print(f"  - call_datetime: {emergency.call_datetime}")
                print(f"  - forward_status: {emergency.forward_status}")
                print(f"  - emergency_type: {emergency.emergency_type}")
                print(f"  - user: {emergency.user}")
                
            # Test the query that's causing issues
            from datetime import datetime, timedelta
            from sqlalchemy import func
            
            days_back = 30
            start_date = datetime.utcnow() - timedelta(days=days_back)
            
            print(f"\nTesting queries with start_date: {start_date}")
            
            # Basic statistics
            total_emergencies = Emergency.query.count()
            print(f"Total emergencies: {total_emergencies}")
            
            recent_emergencies = Emergency.query.filter(Emergency.call_datetime >= start_date).count()
            print(f"Recent emergencies: {recent_emergencies}")
            
            # Status breakdown
            status_counts = db.session.query(
                Emergency.forward_status,
                func.count(Emergency.id).label('count')
            ).group_by(Emergency.forward_status).all()
            
            print(f"Status counts: {status_counts}")
            
        except Exception as e:
            print(f"Error in emergency stats debug: {e}")
            import traceback
            traceback.print_exc()

def debug_blood_inventory():
    """Debug blood inventory issues"""
    with app.app_context():
        print("\n=== Debugging Blood Inventory ===")
        
        try:
            # Check if BloodInventory model exists and has data
            inventory_items = BloodInventory.query.all()
            print(f"Total inventory items in DB: {len(inventory_items)}")
            
            if inventory_items:
                # Check first few items
                for item in inventory_items[:3]:
                    print(f"Inventory {item.id}:")
                    print(f"  - blood_type: {item.blood_type}")
                    print(f"  - units: {item.units}")
                    print(f"  - available_units: {item.available_units}")
                    print(f"  - blood_bank: {item.blood_bank}")
                    
                # Test query parts
                query = BloodInventory.query.order_by(BloodInventory.blood_type, BloodInventory.expiry_date)
                print(f"Ordered query count: {query.count()}")
                
                # Test pagination
                pagination = query.paginate(page=1, per_page=50, error_out=False)
                print(f"Pagination items: {len(pagination.items)}")
                
            else:
                print("No inventory items found - this might be the issue")
                
                # Check if we have any blood banks
                from app.models import BloodBank
                blood_banks = BloodBank.query.all()
                print(f"Blood banks in system: {len(blood_banks)}")
                
        except Exception as e:
            print(f"Error in blood inventory debug: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    debug_emergency_stats()
    debug_blood_inventory()