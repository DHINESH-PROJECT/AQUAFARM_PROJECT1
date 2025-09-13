from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from fish_management.models import Species, FeedPlan, FeedingLog
from datetime import date, time, timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test feeding logs to test calculations'

    def handle(self, *args, **options):
        # Get or create test user
        farmer, created = User.objects.get_or_create(
            username='test_farmer',
            defaults={
                'email': 'farmer@test.com',
                'role': 'farmer',
                'phone': '1234567890',
                'address': 'Test Farm Address'
            }
        )
        
        if created:
            farmer.set_password('testpass123')
            farmer.save()
            self.stdout.write(f"Created test farmer: {farmer.username}")
        
        # Get or create test species
        species, created = Species.objects.get_or_create(
            name='Test Salmon',
            defaults={
                'scientific_name': 'Salmo salar',
                'description': 'Atlantic Salmon for testing',
                'optimal_temp': 15.5,
                'ph_range': '6.5-7.5',
                'feeding_frequency': 3
            }
        )
        
        if created:
            self.stdout.write(f"Created test species: {species.name}")
        
        # Get or create test feed plan
        feed_plan, created = FeedPlan.objects.get_or_create(
            farmer=farmer,
            species=species,
            feed_type='Premium Pellets',
            defaults={
                'quantity_per_day': 5.0,
                'feeding_times': ['08:00', '14:00', '20:00'],
                'start_date': date.today() - timedelta(days=30),
                'end_date': date.today() + timedelta(days=30),
                'notes': 'Test feed plan for calculations'
            }
        )
        
        if created:
            self.stdout.write(f"Created test feed plan: {feed_plan}")
        
        # Create test feeding logs for the last 7 days
        feeding_times = [time(8, 0), time(14, 0), time(20, 0)]
        created_logs = 0
        
        for days_ago in range(7):
            log_date = date.today() - timedelta(days=days_ago)
            
            for feeding_time in feeding_times:
                # Check if log already exists
                if not FeedingLog.objects.filter(
                    feed_plan=feed_plan,
                    feeding_date=log_date,
                    feeding_time=feeding_time
                ).exists():
                    
                    # Create realistic test data
                    quantity_fed = round(random.uniform(1.5, 2.0), 2)  # Varying feed amounts
                    water_temp = round(random.uniform(14.0, 17.0), 1)  # Realistic water temperature
                    ph_level = round(random.uniform(6.8, 7.2), 2)      # Healthy pH range
                    mortality = random.choice([0, 0, 0, 0, 1, 2])      # Mostly zero mortality
                    
                    FeedingLog.objects.create(
                        feed_plan=feed_plan,
                        farmer=farmer,
                        feeding_date=log_date,
                        feeding_time=feeding_time,
                        quantity_fed=quantity_fed,
                        water_temperature=water_temp,
                        ph_level=ph_level,
                        mortality_count=mortality,
                        notes=f'Test log for {log_date} at {feeding_time}'
                    )
                    created_logs += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_logs} test feeding logs'
            )
        )
        
        # Calculate and display statistics
        logs = FeedingLog.objects.filter(feed_plan=feed_plan)
        total_feed = sum(log.quantity_fed for log in logs)
        total_mortality = sum(log.mortality_count for log in logs)
        avg_ph = sum(log.ph_level for log in logs if log.ph_level) / logs.filter(ph_level__isnull=False).count()
        avg_temp = sum(log.water_temperature for log in logs if log.water_temperature) / logs.filter(water_temperature__isnull=False).count()
        
        self.stdout.write(f"\nTest Data Summary:")
        self.stdout.write(f"Total Logs: {logs.count()}")
        self.stdout.write(f"Total Feed Used: {total_feed:.2f} kg")
        self.stdout.write(f"Total Mortality: {total_mortality}")
        self.stdout.write(f"Average pH Level: {avg_ph:.2f}")
        self.stdout.write(f"Average Water Temperature: {avg_temp:.1f}°C")
        
        feed_efficiency = 100 if total_mortality == 0 else max(0, 100 - (total_mortality * 5))
        self.stdout.write(f"Feed Efficiency: {feed_efficiency:.1f}%")
        
        unique_dates = logs.values_list('feeding_date', flat=True).distinct().count()
        daily_average = total_feed / unique_dates if unique_dates > 0 else 0
        self.stdout.write(f"Daily Average Feed: {daily_average:.2f} kg")
