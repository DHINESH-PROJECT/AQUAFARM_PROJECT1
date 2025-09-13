from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import models
from fish_management.models import Inventory, Order, Species
from decimal import Decimal
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test inventory data with orders for testing calculations'

    def handle(self, *args, **options):
        # Get or create test producer
        producer, created = User.objects.get_or_create(
            username='test_producer',
            defaults={
                'email': 'producer@test.com',
                'role': 'producer',
                'phone': '1234567890',
                'address': 'Test Producer Address'
            }
        )
        
        if created:
            producer.set_password('testpass123')
            producer.save()
            self.stdout.write(f"Created test producer: {producer.username}")
        
        # Get or create test farmer for orders
        farmer, created = User.objects.get_or_create(
            username='test_farmer_inventory',
            defaults={
                'email': 'farmer_inventory@test.com',
                'role': 'farmer',
                'phone': '1234567891',
                'address': 'Test Farmer Address'
            }
        )
        
        if created:
            farmer.set_password('testpass123')
            farmer.save()
            self.stdout.write(f"Created test farmer: {farmer.username}")
        
        # Test inventory data
        inventory_data = [
            # Fish items
            {
                'item_type': 'fish',
                'item_name': 'Atlantic Salmon Fingerlings',
                'quantity': 500.0,
                'unit': 'pieces',
                'price_per_unit': Decimal('2.50'),
                'minimum_stock': 100.0
            },
            {
                'item_type': 'fish',
                'item_name': 'Rainbow Trout Juveniles',
                'quantity': 300.0,
                'unit': 'pieces',
                'price_per_unit': Decimal('3.00'),
                'minimum_stock': 75.0
            },
            {
                'item_type': 'fish',
                'item_name': 'Tilapia Fry',
                'quantity': 1000.0,
                'unit': 'pieces',
                'price_per_unit': Decimal('1.25'),
                'minimum_stock': 200.0
            },
            {
                'item_type': 'fish',
                'item_name': 'Catfish Stockers',
                'quantity': 25.0,  # Low stock intentionally
                'unit': 'pieces',
                'price_per_unit': Decimal('4.50'),
                'minimum_stock': 50.0
            },
            
            # Feed items
            {
                'item_type': 'feed',
                'item_name': 'Premium Fish Pellets',
                'quantity': 2500.0,
                'unit': 'kg',
                'price_per_unit': Decimal('1.20'),
                'minimum_stock': 500.0
            },
            {
                'item_type': 'feed',
                'item_name': 'High Protein Starter Feed',
                'quantity': 1200.0,
                'unit': 'kg',
                'price_per_unit': Decimal('1.80'),
                'minimum_stock': 300.0
            },
            {
                'item_type': 'feed',
                'item_name': 'Organic Fish Meal',
                'quantity': 150.0,  # Low stock intentionally
                'unit': 'kg',
                'price_per_unit': Decimal('2.50'),
                'minimum_stock': 200.0
            },
            {
                'item_type': 'feed',
                'item_name': 'Vitamin Supplement',
                'quantity': 75.0,
                'unit': 'kg',
                'price_per_unit': Decimal('5.00'),
                'minimum_stock': 25.0
            },
            
            # Equipment items
            {
                'item_type': 'equipment',
                'item_name': 'Pond Aerator System',
                'quantity': 12.0,
                'unit': 'units',
                'price_per_unit': Decimal('450.00'),
                'minimum_stock': 5.0
            },
            {
                'item_type': 'equipment',
                'item_name': 'Water Quality Test Kit',
                'quantity': 25.0,
                'unit': 'kits',
                'price_per_unit': Decimal('35.00'),
                'minimum_stock': 10.0
            },
            {
                'item_type': 'equipment',
                'item_name': 'Feeding Equipment',
                'quantity': 8.0,
                'unit': 'sets',
                'price_per_unit': Decimal('125.00'),
                'minimum_stock': 3.0
            },
            {
                'item_type': 'equipment',
                'item_name': 'Net Sets (Various Sizes)',
                'quantity': 2.0,  # Low stock intentionally
                'unit': 'sets',
                'price_per_unit': Decimal('75.00'),
                'minimum_stock': 5.0
            },
            {
                'item_type': 'equipment',
                'item_name': 'Temperature Monitors',
                'quantity': 15.0,
                'unit': 'units',
                'price_per_unit': Decimal('28.00'),
                'minimum_stock': 8.0
            }
        ]
        
        created_items = 0
        
        for item_data in inventory_data:
            inventory_item, created = Inventory.objects.get_or_create(
                producer=producer,
                item_name=item_data['item_name'],
                defaults=item_data
            )
            
            if created:
                created_items += 1
                self.stdout.write(f"Created inventory item: {inventory_item.item_name}")
        
        self.stdout.write(f"Created {created_items} new inventory items")
        
        # Create some test orders
        inventory_items = Inventory.objects.filter(producer=producer)
        created_orders = 0
        
        for i in range(8):  # Create 8 test orders
            random_item = random.choice(inventory_items)
            order_quantity = random.uniform(5, 50)
            total_price = order_quantity * float(random_item.price_per_unit)
            
            status_choices = ['pending', 'approved', 'shipped', 'delivered']
            random_status = random.choice(status_choices)
            
            order, created = Order.objects.get_or_create(
                customer=farmer,
                producer=producer,
                inventory_item=random_item,
                quantity=order_quantity,
                defaults={
                    'total_price': Decimal(str(round(total_price, 2))),
                    'status': random_status
                }
            )
            
            if created:
                created_orders += 1
        
        self.stdout.write(f"Created {created_orders} test orders")
        
        # Calculate and display statistics
        total_items = inventory_items.count()
        fish_stock = inventory_items.filter(item_type='fish').count()
        feed_stock = inventory_items.filter(item_type='feed').aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        equipment_count = inventory_items.filter(item_type='equipment').count()
        
        low_stock_items = inventory_items.filter(
            quantity__lte=models.F('minimum_stock')
        )
        low_stock_count = low_stock_items.count()
        
        total_value = sum(
            item.quantity * float(item.price_per_unit) 
            for item in inventory_items
        )
        
        self.stdout.write(f"\nInventory Statistics:")
        self.stdout.write(f"Total Items: {total_items}")
        self.stdout.write(f"Fish Types: {fish_stock}")
        self.stdout.write(f"Feed Stock: {feed_stock:.2f} kg")
        self.stdout.write(f"Equipment Items: {equipment_count}")
        self.stdout.write(f"Low Stock Alerts: {low_stock_count}")
        self.stdout.write(f"Total Inventory Value: ${total_value:.2f}")
        
        if low_stock_items:
            self.stdout.write(f"\nLow Stock Items:")
            for item in low_stock_items:
                self.stdout.write(
                    f"- {item.item_name}: {item.quantity} {item.unit} "
                    f"(Min: {item.minimum_stock})"
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created test inventory data with {created_items} items and {created_orders} orders'
            )
        )
