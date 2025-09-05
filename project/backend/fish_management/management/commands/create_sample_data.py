from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from fish_management.models import *
from datetime import datetime, date, time
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create sample data for fish farming system'
    
    def handle(self, *args, **options):
        # Create users
        self.create_users()
        # Create species
        self.create_species()
        # Create feed plans
        self.create_feed_plans()
        # Create feeding logs
        self.create_feeding_logs()
        # Create inventory
        self.create_inventory()
        # Create orders
        self.create_orders()
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
    
    def create_users(self):
        # Create farmers
        for i in range(1, 6):
            User.objects.get_or_create(
                username=f'farmer{i}',
                defaults={
                    'email': f'farmer{i}@aquacare.com',
                    'role': 'farmer',
                    'phone': f'555-100{i}',
                    'address': f'{i*100} Farm Road, Agriculture City'
                }
            )
        
        # Create producers
        for i in range(1, 4):
            User.objects.get_or_create(
                username=f'producer{i}',
                defaults={
                    'email': f'producer{i}@aquacare.com',
                    'role': 'producer',
                    'phone': f'555-200{i}',
                    'address': f'{i*200} Production Ave, Industry City'
                }
            )
        
        # Create agents
        for i in range(1, 4):
            User.objects.get_or_create(
                username=f'agent{i}',
                defaults={
                    'email': f'agent{i}@aquacare.com',
                    'role': 'agent',
                    'phone': f'555-300{i}',
                    'address': f'{i*300} Delivery Street, Commerce City'
                }
            )
    
    def create_species(self):
        species_data = [
            {
                'name': 'Atlantic Salmon',
                'scientific_name': 'Salmo salar',
                'description': 'Atlantic salmon are anadromous fish prized for their high-quality meat.',
                'optimal_temp': 15.0,
                'ph_range': '6.0-8.0',
                'feeding_frequency': 3
            },
            {
                'name': 'Common Carp',
                'scientific_name': 'Cyprinus carpio',
                'description': 'Common carp are hardy fish tolerating wide conditions.',
                'optimal_temp': 21.0,
                'ph_range': '6.5-8.0',
                'feeding_frequency': 3
            },
            {
                'name': 'Bluegill',
                'scientific_name': 'Lepomis macrochirus',
                'description': 'Bluegill are popular for sport fishing and adapt well to ponds.',
                'optimal_temp': 22.0,
                'ph_range': '6.5-8.5',
                'feeding_frequency': 2
            },
            {
                'name': 'Largemouth Bass',
                'scientific_name': 'Micropterus salmoides',
                'description': 'Largemouth bass are a top predator in freshwater ponds.',
                'optimal_temp': 25.0,
                'ph_range': '6.0-8.0',
                'feeding_frequency': 2
            },
            {
                'name': 'Northern Pike',
                'scientific_name': 'Esox lucius',
                'description': 'Northern pike are aggressive and require large ponds.',
                'optimal_temp': 18.0,
                'ph_range': '6.5-8.0',
                'feeding_frequency': 1
            },
            {
                'name': 'Yellow Perch',
                'scientific_name': 'Perca flavescens',
                'description': 'Yellow perch are valued for their taste and rapid growth.',
                'optimal_temp': 20.0,
                'ph_range': '6.5-8.5',
                'feeding_frequency': 3
            },
            {
                'name': 'Walleye',
                'scientific_name': 'Sander vitreus',
                'description': 'Walleye are popular for their mild flavor and adaptability.',
                'optimal_temp': 17.0,
                'ph_range': '6.0-8.0',
                'feeding_frequency': 2
            },
            {
                'name': 'Sturgeon',
                'scientific_name': 'Acipenseridae',
                'description': 'Sturgeon are ancient fish prized for caviar.',
                'optimal_temp': 16.0,
                'ph_range': '6.5-8.5',
                'feeding_frequency': 1
            },
            {
                'name': 'Pacu',
                'scientific_name': 'Piaractus brachypomus',
                'description': 'Pacu are tropical fish related to piranha, but herbivorous.',
                'optimal_temp': 27.0,
                'ph_range': '6.5-7.5',
                'feeding_frequency': 2
            },
            {
                'name': 'Giant Gourami',
                'scientific_name': 'Osphronemus goramy',
                'description': 'Giant gourami are large, hardy fish for tropical aquaculture.',
                'optimal_temp': 28.0,
                'ph_range': '6.5-8.0',
                'feeding_frequency': 2
            },
            {
                'name': 'Milkfish',
                'scientific_name': 'Chanos chanos',
                'description': 'Milkfish are important in Asian aquaculture for their rapid growth.',
                'optimal_temp': 27.0,
                'ph_range': '7.0-8.5',
                'feeding_frequency': 3
            },
            {
                'name': 'Snakehead',
                'scientific_name': 'Channa striata',
                'description': 'Snakehead are air-breathing fish popular in Asian cuisine.',
                'optimal_temp': 29.0,
                'ph_range': '6.5-8.0',
                'feeding_frequency': 2
            },
            {
                'name': 'Tilapia',
                'scientific_name': 'Oreochromis niloticus',
                'description': 'Tilapia are tropical fish known for fast growth.',
                'optimal_temp': 25.0,
                'ph_range': '6.5-8.5',
                'feeding_frequency': 2
            },
            {
                'name': 'Channel Catfish',
                'scientific_name': 'Ictalurus punctatus',
                'description': 'Channel catfish are bottom-dwelling with excellent feed conversion.',
                'optimal_temp': 26.5,
                'ph_range': '6.5-8.5',
                'feeding_frequency': 2
            },
            {
                'name': 'Common Carp',
                'scientific_name': 'Cyprinus carpio',
                'description': 'Common carp are hardy fish tolerating wide conditions.',
                'optimal_temp': 21.0,
                'ph_range': '6.5-8.0',
                'feeding_frequency': 3
            },
            {
                'name': 'Bluegill',
                'scientific_name': 'Lepomis macrochirus',
                'description': 'Bluegill are popular for sport fishing and adapt well to ponds.',
                'optimal_temp': 22.0,
                'ph_range': '6.5-8.5',
                'feeding_frequency': 2
            },
            {
                'name': 'Largemouth Bass',
                'scientific_name': 'Micropterus salmoides',
                'description': 'Largemouth bass are a top predator in freshwater ponds.',
                'optimal_temp': 25.0,
                'ph_range': '6.0-8.0',
                'feeding_frequency': 2
            },
            {
                'name': 'Northern Pike',
                'scientific_name': 'Esox lucius',
                'description': 'Northern pike are aggressive and require large ponds.',
                'optimal_temp': 18.0,
                'ph_range': '6.5-8.0',
                'feeding_frequency': 1
            },
            {
                'name': 'Yellow Perch',
                'scientific_name': 'Perca flavescens',
                'description': 'Yellow perch are valued for their taste and rapid growth.',
                'optimal_temp': 20.0,
                'ph_range': '6.5-8.5',
                'feeding_frequency': 3
            },
            {
                'name': 'Walleye',
                'scientific_name': 'Sander vitreus',
                'description': 'Walleye are popular for their mild flavor and adaptability.',
                'optimal_temp': 17.0,
                'ph_range': '6.0-8.0',
                'feeding_frequency': 2
            },
            {
                'name': 'Sturgeon',
                'scientific_name': 'Acipenseridae',
                'description': 'Sturgeon are ancient fish prized for caviar.',
                'optimal_temp': 16.0,
                'ph_range': '6.5-8.5',
                'feeding_frequency': 1
            },
            {
                'name': 'Pacu',
                'scientific_name': 'Piaractus brachypomus',
                'description': 'Pacu are tropical fish related to piranha, but herbivorous.',
                'optimal_temp': 27.0,
                'ph_range': '6.5-7.5',
                'feeding_frequency': 2
            },
            {
                'name': 'Giant Gourami',
                'scientific_name': 'Osphronemus goramy',
                'description': 'Giant gourami are large, hardy fish for tropical aquaculture.',
                'optimal_temp': 28.0,
                'ph_range': '6.5-8.0',
                'feeding_frequency': 2
            },
            {
                'name': 'Milkfish',
                'scientific_name': 'Chanos chanos',
                'description': 'Milkfish are important in Asian aquaculture for their rapid growth.',
                'optimal_temp': 27.0,
                'ph_range': '7.0-8.5',
                'feeding_frequency': 3
            },
            {
                'name': 'Snakehead',
                'scientific_name': 'Channa striata',
                'description': 'Snakehead are air-breathing fish popular in Asian cuisine.',
                'optimal_temp': 29.0,
                'ph_range': '6.5-8.0',
                'feeding_frequency': 2
            }
        ]
        
        for data in species_data:
            Species.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
    
    def create_feed_plans(self):
        farmers = User.objects.filter(role='farmer')
        species = Species.objects.all()
        
        feed_types = ['High Protein Pellets', 'Floating Feed', 'Sinking Feed', 'Organic Feed', 'Growth Formula']
        
        for i in range(25):
            FeedPlan.objects.get_or_create(
                farmer=random.choice(farmers),
                species=random.choice(species),
                defaults={
                    'feed_type': random.choice(feed_types),
                    'quantity_per_day': random.uniform(5.0, 50.0),
                    'feeding_times': ['08:00', '14:00', '20:00'],
                    'start_date': date(2024, random.randint(1, 12), random.randint(1, 28)),
                    'end_date': date(2024, random.randint(1, 12), random.randint(1, 28)),
                    'notes': f'Feed plan #{i+1} for optimal growth'
                }
            )
    
    def create_feeding_logs(self):
        feed_plans = FeedPlan.objects.all()
        
        for i in range(50):
            plan = random.choice(feed_plans)
            FeedingLog.objects.get_or_create(
                feed_plan=plan,
                farmer=plan.farmer,
                feeding_date=date(2024, random.randint(1, 12), random.randint(1, 28)),
                feeding_time=time(random.randint(6, 20), random.choice([0, 30])),
                defaults={
                    'quantity_fed': random.uniform(1.0, 10.0),
                    'water_temperature': random.uniform(15.0, 30.0),
                    'ph_level': random.uniform(6.0, 8.5),
                    'mortality_count': random.randint(0, 5),
                    'notes': f'Feeding log entry #{i+1}'
                }
            )
    
    def create_inventory(self):
        producers = User.objects.filter(role='producer')
        items = [
            ('fish', 'Atlantic Salmon Fingerlings', 'pieces', 1.50),
            ('fish', 'Tilapia Juveniles', 'pieces', 0.75),
            ('feed', 'High Protein Fish Feed', 'kg', 2.25),
            ('feed', 'Organic Fish Pellets', 'kg', 3.50),
            ('equipment', 'Aerator Pump', 'units', 150.00),
            ('equipment', 'Water Filter System', 'units', 300.00),
            ('equipment', 'pH Test Kit', 'kits', 25.00),
            ('equipment', 'Feeding Timer', 'units', 45.00)
        ]
        
        for producer in producers:
            for item_type, name, unit, price in items:
                Inventory.objects.get_or_create(
                    producer=producer,
                    item_name=name,
                    defaults={
                        'item_type': item_type,
                        'quantity': random.uniform(50, 1000),
                        'unit': unit,
                        'price_per_unit': price,
                        'minimum_stock': random.uniform(10, 100)
                    }
                )
    
    def create_orders(self):
        farmers = User.objects.filter(role='farmer')
        inventory_items = Inventory.objects.all()
        
        for i in range(20):
            item = random.choice(inventory_items)
            quantity = random.uniform(1, 50)
            total_price = quantity * float(item.price_per_unit)
            
            Order.objects.get_or_create(
                customer=random.choice(farmers),
                producer=item.producer,
                inventory_item=item,
                defaults={
                    'quantity': quantity,
                    'total_price': total_price,
                    'status': random.choice(['pending', 'approved', 'shipped', 'delivered'])
                }
            )