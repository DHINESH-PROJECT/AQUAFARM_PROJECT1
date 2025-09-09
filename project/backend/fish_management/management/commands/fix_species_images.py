from django.core.management.base import BaseCommand
from fish_management.models import Species

class Command(BaseCommand):
    help = 'Fix species image paths in database'
    
    def handle(self, *args, **options):
        # Update Atlantic Salmon to use the correct image path
        try:
            atlantic_salmon = Species.objects.get(name='Atlantic Salmon')
            atlantic_salmon.image = 'species/atlantic_salmon.jpeg'
            atlantic_salmon.save()
            self.stdout.write(self.style.SUCCESS(f'Updated Atlantic Salmon image path'))
        except Species.DoesNotExist:
            self.stdout.write(self.style.WARNING('Atlantic Salmon not found in database'))
        
        # Clear invalid image paths for other species (they'll use the default fish logo)
        species_with_invalid_paths = Species.objects.exclude(name='Atlantic Salmon')
        for species in species_with_invalid_paths:
            if species.image and 'static' in str(species.image):
                species.image = None
                species.save()
                self.stdout.write(self.style.SUCCESS(f'Cleared invalid image path for {species.name}'))
        
        self.stdout.write(self.style.SUCCESS('Species image paths fixed successfully!'))
