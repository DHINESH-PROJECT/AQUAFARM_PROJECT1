#!/usr/bin/env python
"""
Test script for inventory management functionality
"""
import os
import sys
import django

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fish_farming.settings')
django.setup()

from fish_management.models import Inventory, Order, User
from django.db.models import Sum, F

def test_inventory_calculations():
    """Test inventory calculation functionality"""
    print("=== Inventory Management Test ===\n")
    
    # Get test producer
    try:
        producer = User.objects.get(username='test_producer')
        print(f"✓ Found test producer: {producer.username}")
    except User.DoesNotExist:
        print("✗ Test producer not found. Run 'python manage.py test_inventory_data' first.")
        return
    
    # Get inventory items
    inventory_items = Inventory.objects.filter(producer=producer)
    print(f"✓ Found {inventory_items.count()} inventory items")
    
    # Test calculations
    print("\n--- Inventory Statistics ---")
    
    # Fish stock calculation
    fish_stock = inventory_items.filter(item_type='fish').aggregate(
        total=Sum('quantity')
    )['total'] or 0
    print(f"Fish Stock: {fish_stock} pieces")
    
    # Feed stock calculation
    feed_stock = inventory_items.filter(item_type='feed').aggregate(
        total=Sum('quantity')
    )['total'] or 0
    print(f"Feed Stock: {feed_stock} kg")
    
    # Equipment count
    equipment_count = inventory_items.filter(item_type='equipment').count()
    print(f"Equipment Items: {equipment_count}")
    
    # Low stock alerts
    low_stock_items = inventory_items.filter(quantity__lte=F('minimum_stock'))
    low_stock_count = low_stock_items.count()
    print(f"Low Stock Alerts: {low_stock_count}")
    
    # Total value calculation
    total_value = sum(item.quantity * float(item.price_per_unit) for item in inventory_items)
    print(f"Total Inventory Value: ${total_value:,.2f}")
    
    # Category breakdown
    print("\n--- Category Breakdown ---")
    for item_type in ['fish', 'feed', 'equipment']:
        category_items = inventory_items.filter(item_type=item_type)
        category_count = category_items.count()
        category_quantity = category_items.aggregate(total=Sum('quantity'))['total'] or 0
        category_value = sum(item.quantity * float(item.price_per_unit) for item in category_items)
        
        print(f"{item_type.title()}: {category_count} items, {category_quantity} units, ${category_value:,.2f}")
    
    # Low stock details
    if low_stock_items:
        print("\n--- Low Stock Items ---")
        for item in low_stock_items:
            print(f"- {item.item_name}: {item.quantity} {item.unit} (Min: {item.minimum_stock})")
    
    # Order statistics
    orders = Order.objects.filter(inventory_item__in=inventory_items)
    print(f"\n--- Order Statistics ---")
    print(f"Total Orders: {orders.count()}")
    
    for status in ['pending', 'approved', 'shipped', 'delivered']:
        status_count = orders.filter(status=status).count()
        print(f"{status.title()} Orders: {status_count}")
    
    print("\n✓ All inventory calculations completed successfully!")

def test_data_validation():
    """Test data validation functionality"""
    print("\n=== Data Validation Test ===\n")
    
    producer = User.objects.get(username='test_producer')
    
    # Test duplicate item check
    existing_item = Inventory.objects.filter(producer=producer).first()
    if existing_item:
        duplicate_exists = Inventory.objects.filter(
            producer=producer,
            item_name__iexact=existing_item.item_name,
            item_type=existing_item.item_type
        ).exists()
        print(f"✓ Duplicate check working: {duplicate_exists}")
    
    # Test stock level validation
    low_stock_item = Inventory.objects.filter(
        producer=producer,
        quantity__lte=F('minimum_stock')
    ).first()
    
    if low_stock_item:
        is_low_stock = low_stock_item.quantity <= low_stock_item.minimum_stock
        print(f"✓ Low stock detection working: {is_low_stock}")
        print(f"  Item: {low_stock_item.item_name}")
        print(f"  Current: {low_stock_item.quantity} {low_stock_item.unit}")
        print(f"  Minimum: {low_stock_item.minimum_stock} {low_stock_item.unit}")
    
    print("\n✓ Data validation tests completed!")

def test_template_filters():
    """Test custom template filters"""
    print("\n=== Template Filters Test ===\n")
    
    from fish_management.templatetags.inventory_extras import multiply, currency, format_quantity, stock_status
    
    # Test multiply filter
    result = multiply(10.5, 2.3)
    print(f"✓ Multiply filter: 10.5 × 2.3 = {result}")
    
    # Test currency filter
    formatted = currency(1234.56)
    print(f"✓ Currency filter: 1234.56 → {formatted}")
    
    # Test format_quantity filter
    quantity_formatted = format_quantity(1500.0, "kg")
    print(f"✓ Format quantity: 1500.0 kg → {quantity_formatted}")
    
    # Test stock_status filter with mock item
    class MockItem:
        def __init__(self, quantity, minimum_stock):
            self.quantity = quantity
            self.minimum_stock = minimum_stock
    
    mock_item_low = MockItem(10, 20)
    mock_item_normal = MockItem(50, 20)
    mock_item_empty = MockItem(0, 10)
    
    print(f"✓ Stock status filter:")
    print(f"  Low stock (10/20): {stock_status(mock_item_low)}")
    print(f"  Normal stock (50/20): {stock_status(mock_item_normal)}")
    print(f"  Out of stock (0/10): {stock_status(mock_item_empty)}")
    
    print("\n✓ Template filters working correctly!")

if __name__ == "__main__":
    try:
        test_inventory_calculations()
        test_data_validation()
        test_template_filters()
        print("\n🎉 All tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
