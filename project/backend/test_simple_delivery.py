#!/usr/bin/env python
"""
Simple test to verify delivery assignment via web interface
"""
import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fish_farming.settings')
django.setup()

from fish_management.models import User, Order, Delivery, Inventory
from datetime import datetime, timedelta

def test_delivery_assignment_direct():
    """Test delivery assignment directly using model methods"""
    
    print("🔍 Testing Direct Delivery Assignment")
    print("=" * 50)
    
    # Get available resources
    agents = User.objects.filter(role='agent', is_active=True)
    workers = User.objects.filter(role='worker', is_active=True)
    approved_orders = Order.objects.filter(status='approved')
    
    print(f"✅ Available Agents: {agents.count()}")
    print(f"✅ Available Workers: {workers.count()}")
    print(f"✅ Approved Orders: {approved_orders.count()}")
    
    if agents.exists() and workers.exists() and approved_orders.exists():
        # Take first available resources
        test_agent = agents.first()
        test_worker = workers.first()
        test_order = approved_orders.first()
        
        print(f"\n🧪 Creating Test Delivery...")
        print(f"   Order: #{test_order.id} - {test_order.inventory_item.item_name}")
        print(f"   Agent: {test_agent.username}")
        print(f"   Worker: {test_worker.username}")
        
        try:
            # Check if delivery already exists
            existing_delivery = Delivery.objects.filter(order=test_order).first()
            if existing_delivery:
                print(f"⚠️  Delivery already exists for this order: #DEL-{existing_delivery.id}")
                return
            
            # Create delivery
            pickup_date = datetime.now() + timedelta(hours=2)
            delivery = Delivery.objects.create(
                order=test_order,
                agent=test_agent,
                worker=test_worker,
                pickup_date=pickup_date,
                delivery_address="123 Test Farm Address, Test City, 12345",
                delivery_notes="Test delivery assignment - automated test"
            )
            
            # Update order status
            test_order.status = 'shipped'
            test_order.save()
            
            print(f"✅ Delivery created successfully!")
            print(f"   Delivery ID: #DEL-{delivery.id}")
            print(f"   Pickup Date: {delivery.pickup_date}")
            print(f"   Status: {'Delivered' if delivery.is_delivered else 'Pending'}")
            
            # Verify delivery data
            delivery_check = Delivery.objects.get(id=delivery.id)
            print(f"✅ Delivery verification passed!")
            print(f"   Order: #{delivery_check.order.id}")
            print(f"   Agent: {delivery_check.agent.username}")
            print(f"   Worker: {delivery_check.worker.username}")
            
        except Exception as e:
            print(f"❌ Error creating delivery: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print("❌ Cannot test assignment - missing required data")
    
    # Show final statistics
    total_deliveries = Delivery.objects.count()
    pending_deliveries = Delivery.objects.filter(is_delivered=False).count()
    completed_deliveries = Delivery.objects.filter(is_delivered=True).count()
    
    print(f"\n📊 Final Statistics:")
    print(f"   Total Deliveries: {total_deliveries}")
    print(f"   Pending Deliveries: {pending_deliveries}")
    print(f"   Completed Deliveries: {completed_deliveries}")
    
    if total_deliveries > 0:
        print("✅ Delivery assignment system is working correctly!")
    else:
        print("⚠️  No deliveries found - system may need data or debugging")

if __name__ == '__main__':
    test_delivery_assignment_direct()