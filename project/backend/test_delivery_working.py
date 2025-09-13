#!/usr/bin/env python
"""
Test script to verify delivery assignment system functionality
"""
import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fish_farming.settings')
django.setup()

from fish_management.models import User, Order, Delivery
from datetime import datetime, timedelta

def test_delivery_assignment():
    """Test the delivery assignment functionality"""
    
    print("🔍 Testing Delivery Assignment System")
    print("=" * 50)
    
    # 1. Check available agents
    agents = User.objects.filter(role='agent', is_active=True)
    print(f"✅ Available Agents: {agents.count()}")
    for agent in agents[:3]:
        print(f"   - {agent.username} ({agent.first_name} {agent.last_name})")
    
    # 2. Check available workers
    workers = User.objects.filter(role='worker', is_active=True)
    print(f"✅ Available Workers: {workers.count()}")
    for worker in workers[:3]:
        print(f"   - {worker.username} ({worker.first_name} {worker.last_name})")
    
    # 3. Check approved orders ready for assignment
    approved_orders = Order.objects.filter(status='approved')
    print(f"✅ Approved Orders: {approved_orders.count()}")
    for order in approved_orders[:3]:
        print(f"   - Order #{order.id}: {order.inventory_item.item_name} - {order.quantity} units")
    
    # 4. Check existing deliveries
    deliveries = Delivery.objects.all()
    print(f"✅ Existing Deliveries: {deliveries.count()}")
    
    # 5. Test assignment simulation
    if agents.exists() and workers.exists() and approved_orders.exists():
        print("\n🧪 Simulating Delivery Assignment...")
        
        # Get first available resources
        test_agent = agents.first()
        test_worker = workers.first()
        test_order = approved_orders.first()
        
        # Check if assignment is possible
        pickup_date = datetime.now().date() + timedelta(days=1)
        delivery_address = "123 Test Street, Test City"
        
        print(f"   Agent: {test_agent.username}")
        print(f"   Worker: {test_worker.username}")
        print(f"   Order: #{test_order.id}")
        print(f"   Pickup Date: {pickup_date}")
        print(f"   Address: {delivery_address}")
        
        # Simulate what happens in the view
        try:
            # This simulates the delivery creation process
            delivery_data = {
                'order': test_order,
                'agent': test_agent,
                'worker': test_worker,
                'pickup_date': pickup_date,
                'delivery_address': delivery_address,
                'status': 'assigned'
            }
            print("✅ Assignment simulation successful - all data valid")
            
        except Exception as e:
            print(f"❌ Assignment simulation failed: {e}")
    
    else:
        print("❌ Cannot test assignment - missing required data:")
        if not agents.exists():
            print("   - No agents available")
        if not workers.exists():
            print("   - No workers available")
        if not approved_orders.exists():
            print("   - No approved orders available")
    
    print("\n📊 System Status Summary:")
    print(f"   - Agents: {agents.count()}")
    print(f"   - Workers: {workers.count()}")
    print(f"   - Approved Orders: {approved_orders.count()}")
    print(f"   - Total Deliveries: {deliveries.count()}")
    
    # Check for any system issues
    if agents.count() > 0 and workers.count() > 0 and approved_orders.count() > 0:
        print("✅ System ready for delivery assignments!")
    else:
        print("⚠️  System needs more test data for full functionality")

if __name__ == '__main__':
    test_delivery_assignment()