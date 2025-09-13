#!/usr/bin/env python
"""
Test script to verify order calculations and statistics
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
from django.db.models import Count, Sum, Avg, Max, Min, FloatField

def test_order_calculations():
    """Test all order calculations and statistics"""
    
    print("🔍 Testing Order Calculations & Statistics")
    print("=" * 50)
    
    # Get all orders
    orders = Order.objects.all().select_related('customer', 'producer', 'inventory_item')
    
    print(f"✅ Total Orders Found: {orders.count()}")
    
    if orders.count() == 0:
        print("❌ No orders found for testing calculations")
        return
    
    # Test basic statistics
    order_stats = orders.aggregate(
        total_orders=Count('id'),
        total_revenue=Sum('total_price') or 0,
        average_order_value=Avg('total_price') or 0,
        total_quantity=Sum('quantity') or 0,
        max_order_value=Max('total_price') or 0,
        min_order_value=Min('total_price') or 0
    )
    
    print(f"📊 Basic Statistics:")
    print(f"   Total Orders: {order_stats['total_orders']}")
    print(f"   Total Revenue: ${order_stats['total_revenue']:.2f}")
    print(f"   Average Order Value: ${order_stats['average_order_value']:.2f}")
    print(f"   Total Quantity: {order_stats['total_quantity']:.1f}")
    print(f"   Max Order Value: ${order_stats['max_order_value']:.2f}")
    print(f"   Min Order Value: ${order_stats['min_order_value']:.2f}")
    
    # Test status breakdown
    status_breakdown = orders.values('status').annotate(
        count=Count('id'),
        total_value=Sum('total_price'),
        avg_value=Avg('total_price'),
        total_qty=Sum('quantity')
    ).order_by('status')
    
    print(f"\n📈 Status Breakdown:")
    for status in status_breakdown:
        print(f"   {status['status'].title()}: {status['count']} orders, ${status['total_value']:.2f} total")
    
    # Test item statistics (fixed version)
    item_stats = orders.values('inventory_item__item_name', 'inventory_item__unit').annotate(
        order_count=Count('id'),
        total_quantity=Sum('quantity'),
        total_value=Sum('total_price'),
        avg_price_per_unit=Avg('inventory_item__price_per_unit', output_field=FloatField())
    ).order_by('-total_value')[:5]  # Top 5 items
    
    print(f"\n🎯 Top Items:")
    for item in item_stats:
        print(f"   {item['inventory_item__item_name']}: {item['order_count']} orders, {item['total_quantity']:.1f} {item['inventory_item__unit']}")
        print(f"      Total Value: ${item['total_value']:.2f}, Avg Price: ${item['avg_price_per_unit']:.2f}")
    
    # Test customer statistics
    customer_stats = orders.values('customer__username', 'customer__role').annotate(
        order_count=Count('id'),
        total_spent=Sum('total_price'),
        avg_order_value=Avg('total_price'),
        last_order_date=Max('order_date')
    ).order_by('-total_spent')[:5]  # Top 5 customers
    
    print(f"\n👥 Top Customers:")
    for customer in customer_stats:
        print(f"   {customer['customer__username']} ({customer['customer__role'].title()}): {customer['order_count']} orders")
        print(f"      Total Spent: ${customer['total_spent']:.2f}, Avg: ${customer['avg_order_value']:.2f}")
    
    # Calculate rates
    pending_orders = orders.filter(status='pending').count()
    approved_orders = orders.filter(status='approved').count()
    delivered_orders = orders.filter(status='delivered').count()
    rejected_orders = orders.filter(status='rejected').count()
    
    total_processed = pending_orders + approved_orders + rejected_orders
    approval_rate = (approved_orders / max(total_processed, 1)) * 100
    completion_rate = (delivered_orders / max(order_stats['total_orders'], 1)) * 100
    
    print(f"\n📊 Performance Metrics:")
    print(f"   Approval Rate: {approval_rate:.1f}%")
    print(f"   Completion Rate: {completion_rate:.1f}%")
    
    # Test individual order calculations
    print(f"\n🔢 Sample Order Calculations:")
    for order in orders[:3]:
        calculated_total = float(order.quantity) * float(order.inventory_item.price_per_unit)
        stored_total = float(order.total_price)
        
        print(f"   Order #{order.id}: {order.quantity} × ${order.inventory_item.price_per_unit} = ${calculated_total:.2f}")
        print(f"      Stored Total: ${stored_total:.2f} {'✅' if abs(calculated_total - stored_total) < 0.01 else '❌'}")
    
    print(f"\n✅ All calculations completed successfully!")
    print(f"📊 Orders page ready with comprehensive analytics!")

if __name__ == '__main__':
    test_order_calculations()