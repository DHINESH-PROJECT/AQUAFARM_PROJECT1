from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from fish_management.models import Order, Inventory
from decimal import Decimal
import random
from datetime import datetime, timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test data for delivery assignment including agents, workers, and approved orders'

    def handle(self, *args, **options):
        # Create test agents
        agents_data = [
            {'username': 'agent1', 'email': 'agent1@test.com', 'phone': '+1-555-0101'},
            {'username': 'agent2', 'email': 'agent2@test.com', 'phone': '+1-555-0102'},
            {'username': 'agent3', 'email': 'agent3@test.com', 'phone': '+1-555-0103'},
        ]
        
        created_agents = 0
        for agent_data in agents_data:
            agent, created = User.objects.get_or_create(
                username=agent_data['username'],
                defaults={
                    'email': agent_data['email'],
                    'role': 'agent',
                    'phone': agent_data['phone'],
                    'address': f"Agent Address - {agent_data['username']}",
                    'is_active': True
                }
            )
            
            if created:
                agent.set_password('testpass123')
                agent.save()
                created_agents += 1
                self.stdout.write(f"Created agent: {agent.username}")
        
        # Create test workers
        workers_data = [
            {'username': 'worker1', 'email': 'worker1@test.com', 'phone': '+1-555-0201'},
            {'username': 'worker2', 'email': 'worker2@test.com', 'phone': '+1-555-0202'},
            {'username': 'worker3', 'email': 'worker3@test.com', 'phone': '+1-555-0203'},
            {'username': 'worker4', 'email': 'worker4@test.com', 'phone': '+1-555-0204'},
        ]
        
        created_workers = 0
        for worker_data in workers_data:
            worker, created = User.objects.get_or_create(
                username=worker_data['username'],
                defaults={
                    'email': worker_data['email'],
                    'role': 'worker',
                    'phone': worker_data['phone'],
                    'address': f"Worker Address - {worker_data['username']}",
                    'is_active': True
                }
            )
            
            if created:
                worker.set_password('testpass123')
                worker.save()
                created_workers += 1
                self.stdout.write(f"Created worker: {worker.username}")
        
        # Get test producer and farmer
        try:
            producer = User.objects.get(username='test_producer')
            farmer = User.objects.get(username='test_farmer_inventory')
            self.stdout.write(f"Found producer: {producer.username} and farmer: {farmer.username}")
        except User.DoesNotExist:
            self.stdout.write("Test producer or farmer not found. Run test_inventory_data first.")
            return
        
        # Get inventory items
        inventory_items = Inventory.objects.filter(producer=producer)
        
        if not inventory_items.exists():
            self.stdout.write("No inventory items found. Run test_inventory_data first.")
            return
        
        # Create approved orders for delivery assignment
        created_orders = 0
        
        for i in range(6):  # Create 6 test orders
            random_item = random.choice(inventory_items)
            order_quantity = random.uniform(5, 20)
            total_price = order_quantity * float(random_item.price_per_unit)
            
            order, created = Order.objects.get_or_create(
                customer=farmer,
                producer=producer,
                inventory_item=random_item,
                quantity=order_quantity,
                defaults={
                    'total_price': Decimal(str(round(total_price, 2))),
                    'status': 'approved'  # Set to approved so they can be assigned
                }
            )
            
            if created:
                created_orders += 1
                self.stdout.write(f"Created approved order: Order #{order.id} - {random_item.item_name}")
        
        # Also create some pending orders (not available for assignment)
        for i in range(3):
            random_item = random.choice(inventory_items)
            order_quantity = random.uniform(3, 15)
            total_price = order_quantity * float(random_item.price_per_unit)
            
            Order.objects.get_or_create(
                customer=farmer,
                producer=producer,
                inventory_item=random_item,
                quantity=order_quantity,
                defaults={
                    'total_price': Decimal(str(round(total_price, 2))),
                    'status': 'pending'  # These won't be available for assignment
                }
            )
        
        # Statistics
        total_agents = User.objects.filter(role='agent', is_active=True).count()
        total_workers = User.objects.filter(role='worker', is_active=True).count()
        approved_orders = Order.objects.filter(status='approved').count()
        pending_orders = Order.objects.filter(status='pending').count()
        
        self.stdout.write(f"\nDelivery Assignment Data Summary:")
        self.stdout.write(f"Active Agents: {total_agents}")
        self.stdout.write(f"Active Workers: {total_workers}")
        self.stdout.write(f"Approved Orders (available for assignment): {approved_orders}")
        self.stdout.write(f"Pending Orders: {pending_orders}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created delivery test data: {created_agents} agents, {created_workers} workers, {created_orders} approved orders'
            )
        )