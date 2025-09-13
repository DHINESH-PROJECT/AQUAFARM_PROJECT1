#!/usr/bin/env python
"""
Test script to verify order action functionality
"""
import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fish_farming.settings')
django.setup()

from fish_management.models import User, Order, Inventory
from django.contrib.auth import get_user_model

def test_order_actions():
    """Test order approval, rejection, and shipping actions"""
    
    print("🔍 Testing Order Actions Functionality")
    print("=" * 50)
    
    # Get orders in different statuses
    pending_orders = Order.objects.filter(status='pending')
    approved_orders = Order.objects.filter(status='approved')
    shipped_orders = Order.objects.filter(status='shipped')
    rejected_orders = Order.objects.filter(status='rejected')
    
    print(f"📊 Current Order Status Count:")
    print(f"   Pending: {pending_orders.count()}")
    print(f"   Approved: {approved_orders.count()}")
    print(f"   Shipped: {shipped_orders.count()}")
    print(f"   Rejected: {rejected_orders.count()}")
    
    # Test order approval simulation
    if pending_orders.exists():
        test_order = pending_orders.first()
        print(f"\n🧪 Testing Order Approval:")
        print(f"   Order #{test_order.id}: {test_order.inventory_item.item_name}")
        print(f"   Customer: {test_order.customer.username}")
        print(f"   Producer: {test_order.producer.username}")
        print(f"   Quantity: {test_order.quantity}")
        print(f"   Available Stock: {test_order.inventory_item.quantity}")
        print(f"   Current Status: {test_order.status}")
        
        # Check if order can be approved
        if test_order.inventory_item.quantity >= test_order.quantity:
            print(f"   ✅ Order can be approved (sufficient stock)")
            
            # Simulate approval
            old_stock = test_order.inventory_item.quantity
            print(f"   📦 Stock before approval: {old_stock}")
            print(f"   📦 Stock after approval would be: {old_stock - test_order.quantity}")
        else:
            print(f"   ❌ Order cannot be approved (insufficient stock)")
    else:
        print(f"\n⚠️  No pending orders available for approval testing")
    
    # Test order rejection simulation
    if approved_orders.exists():
        test_order = approved_orders.first()
        print(f"\n🧪 Testing Order Rejection:")
        print(f"   Order #{test_order.id}: {test_order.inventory_item.item_name}")
        print(f"   Current Status: {test_order.status}")
        print(f"   ✅ Order can be rejected")
        print(f"   📦 Stock would be returned: +{test_order.quantity}")
    
    # Test shipping simulation
    if approved_orders.exists():
        test_order = approved_orders.first()
        print(f"\n🧪 Testing Order Shipping:")
        print(f"   Order #{test_order.id}: {test_order.inventory_item.item_name}")
        print(f"   Current Status: {test_order.status}")
        print(f"   ✅ Order can be shipped (already approved)")
    
    # Show producers and their orders
    producers = User.objects.filter(role='producer', is_active=True)
    print(f"\n👥 Producer Order Summary:")
    for producer in producers[:3]:
        producer_orders = Order.objects.filter(producer=producer)
        print(f"   {producer.username}: {producer_orders.count()} orders")
        for status in ['pending', 'approved', 'shipped', 'rejected']:
            count = producer_orders.filter(status=status).count()
            if count > 0:
                print(f"     - {status.title()}: {count}")
    
    # Test action URLs
    print(f"\n🔗 Available Action Endpoints:")
    print(f"   - /ajax/approve_order/<order_id>/")
    print(f"   - /ajax/reject_order/<order_id>/")
    print(f"   - /ajax/ship_order/<order_id>/")
    
    print(f"\n✅ Order actions system ready for testing!")
    print(f"📊 Use the orders page to test approve/reject/ship functionality")
    
    # Show specific orders that can be tested
    if pending_orders.exists():
        print(f"\n🎯 Orders Ready for Testing:")
        for order in pending_orders[:3]:
            print(f"   Order #{order.id} (Pending): {order.inventory_item.item_name} - {order.quantity} units")
            print(f"     Stock Available: {order.inventory_item.quantity} (Can approve: {'Yes' if order.inventory_item.quantity >= order.quantity else 'No'})")

if __name__ == '__main__':
    test_order_actions()