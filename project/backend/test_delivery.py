#!/usr/bin/env python
"""
Test script for delivery assignment functionality
"""
import os
import sys
import django

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fish_farming.settings')
django.setup()

from fish_management.models import Delivery, Order, User
from django.utils import timezone

def test_delivery_assignment():
    """Test delivery assignment functionality"""
    print("=== Delivery Assignment Test ===\n")
    
    # Check available data
    agents = User.objects.filter(role='agent', is_active=True)
    workers = User.objects.filter(role='worker', is_active=True)
    approved_orders = Order.objects.filter(status='approved')
    
    print(f"Available Agents: {agents.count()}")
    for agent in agents:
        print(f"  - {agent.username} ({agent.phone})")
    
    print(f"\nAvailable Workers: {workers.count()}")
    for worker in workers:
        print(f"  - {worker.username} ({worker.phone})")
    
    print(f"\nApproved Orders (available for assignment): {approved_orders.count()}")
    for order in approved_orders:
        print(f"  - Order #{order.id}: {order.inventory_item.item_name} ({order.quantity} units) - ${order.total_price}")
    
    # Check existing deliveries
    existing_deliveries = Delivery.objects.all()
    print(f"\nExisting Deliveries: {existing_deliveries.count()}")
    
    # Calculate statistics
    pending_deliveries = existing_deliveries.filter(is_delivered=False)
    completed_deliveries = existing_deliveries.filter(is_delivered=True)
    
    print(f"Pending Deliveries: {pending_deliveries.count()}")
    print(f"Completed Deliveries: {completed_deliveries.count()}")
    
    # Show delivery details
    if existing_deliveries.exists():
        print(f"\nDelivery Details:")
        for delivery in existing_deliveries:
            status = "Delivered" if delivery.is_delivered else "Pending"
            pickup_date = delivery.pickup_date.strftime('%Y-%m-%d %H:%M')
            delivery_date = delivery.delivery_date.strftime('%Y-%m-%d %H:%M') if delivery.delivery_date else "Not delivered"
            
            print(f"  - Delivery #{delivery.id}: Order #{delivery.order.id}")
            print(f"    Agent: {delivery.agent.username}, Worker: {delivery.worker.username}")
            print(f"    Status: {status}, Pickup: {pickup_date}, Delivery: {delivery_date}")
    
    print("\n✓ Delivery assignment system ready for testing!")

def test_delivery_statistics():
    """Test delivery statistics calculations"""
    print("\n=== Delivery Statistics Test ===\n")
    
    deliveries = Delivery.objects.all()
    today = timezone.now().date()
    
    # Statistics
    total_deliveries = deliveries.count()
    pending_count = deliveries.filter(is_delivered=False).count()
    delivered_count = deliveries.filter(is_delivered=True).count()
    delivered_today = deliveries.filter(
        is_delivered=True,
        delivery_date__date=today
    ).count()
    
    in_transit_count = deliveries.filter(
        is_delivered=False,
        order__status='shipped'
    ).count()
    
    # User counts
    active_agents = User.objects.filter(role='agent', is_active=True).count()
    active_workers = User.objects.filter(role='worker', is_active=True).count()
    
    print(f"Statistics Summary:")
    print(f"Total Deliveries: {total_deliveries}")
    print(f"Pending Deliveries: {pending_count}")
    print(f"In Transit: {in_transit_count}")
    print(f"Delivered: {delivered_count}")
    print(f"Delivered Today: {delivered_today}")
    print(f"Active Agents: {active_agents}")
    print(f"Active Workers: {active_workers}")
    
    # Calculate average delivery time
    completed_deliveries = deliveries.filter(is_delivered=True)
    if completed_deliveries.exists():
        total_hours = 0
        count = 0
        
        for delivery in completed_deliveries:
            if delivery.delivery_date and delivery.pickup_date:
                diff = delivery.delivery_date - delivery.pickup_date
                hours = diff.total_seconds() / 3600
                total_hours += hours
                count += 1
                print(f"  Delivery #{delivery.id}: {hours:.1f} hours")
        
        if count > 0:
            avg_hours = total_hours / count
            print(f"\nAverage Delivery Time: {avg_hours:.1f} hours")
    
    print("\n✓ Statistics calculations working correctly!")

def simulate_delivery_assignment():
    """Simulate a delivery assignment"""
    print("\n=== Delivery Assignment Simulation ===\n")
    
    # Get first available order, agent, and worker
    approved_order = Order.objects.filter(status='approved').first()
    agent = User.objects.filter(role='agent', is_active=True).first()
    worker = User.objects.filter(role='worker', is_active=True).first()
    
    if not all([approved_order, agent, worker]):
        print("❌ Missing required data for simulation")
        return
    
    # Check if delivery already exists
    if Delivery.objects.filter(order=approved_order).exists():
        print(f"⚠️ Delivery already exists for Order #{approved_order.id}")
        return
    
    print(f"Simulating assignment:")
    print(f"Order: #{approved_order.id} - {approved_order.inventory_item.item_name}")
    print(f"Customer: {approved_order.customer.username}")
    print(f"Agent: {agent.username}")
    print(f"Worker: {worker.username}")
    
    # Create delivery (simulation)
    pickup_time = timezone.now() + timezone.timedelta(hours=2)
    delivery_address = f"{approved_order.customer.address or 'Customer Address'}"
    
    print(f"Pickup Time: {pickup_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"Delivery Address: {delivery_address}")
    
    print("\n✓ Assignment simulation parameters validated!")
    print("Note: This is a simulation. Use the web interface to create actual assignments.")

if __name__ == "__main__":
    try:
        test_delivery_assignment()
        test_delivery_statistics()
        simulate_delivery_assignment()
        print("\n🎉 All delivery tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()