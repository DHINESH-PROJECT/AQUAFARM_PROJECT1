from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    ROLE_CHOICES = [
        ('farmer', 'Farmer'),
        ('producer', 'Producer'),
        ('agent', 'Agent'),
        ('worker', 'Worker'),
    ]
    

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='farmer')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='fish_management_user_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='fish_management_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return f"{self.username} - {self.role}"

class Species(models.Model):
    name = models.CharField(max_length=100)
    scientific_name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='species/', blank=True, null=True)
    optimal_temp = models.FloatField(help_text="Optimal temperature in Celsius")
    ph_range = models.CharField(max_length=20, help_text="pH range (e.g., 6.5-7.5)")
    feeding_frequency = models.IntegerField(help_text="Times per day", validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Species"

    def __str__(self):
        return self.name

class FeedPlan(models.Model):
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'farmer'})
    species = models.ForeignKey(Species, on_delete=models.CASCADE)
    feed_type = models.CharField(max_length=100)
    quantity_per_day = models.FloatField(help_text="Quantity in kg per day")
    feeding_times = models.JSONField(help_text="List of feeding times")
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.farmer.username} - {self.species.name} - {self.feed_type}"

class FeedingLog(models.Model):
    feed_plan = models.ForeignKey(FeedPlan, on_delete=models.CASCADE)
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'farmer'})
    feeding_date = models.DateField()
    feeding_time = models.TimeField()
    quantity_fed = models.FloatField(help_text="Actual quantity fed in kg")
    water_temperature = models.FloatField(blank=True, null=True)
    ph_level = models.FloatField(blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(14)])
    mortality_count = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.farmer.username} - {self.feeding_date} - {self.feeding_time}"

class Inventory(models.Model):
    ITEM_TYPES = [
        ('fish', 'Fish'),
        ('feed', 'Feed'),
        ('equipment', 'Equipment'),
    ]
    
    producer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'producer'})
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    item_name = models.CharField(max_length=100)
    quantity = models.FloatField()
    unit = models.CharField(max_length=20)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_stock = models.FloatField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventory"

    def __str__(self):
        return f"{self.item_name} - {self.quantity} {self.unit}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
    ]
    
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    producer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'producer'}, related_name='producer_orders')
    inventory_item = models.ForeignKey(Inventory, on_delete=models.CASCADE)
    quantity = models.FloatField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    order_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username}"

class Delivery(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    agent = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'agent'}, related_name='deliveries_as_agent')
    worker = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'worker'}, related_name='deliveries_as_worker')
    pickup_date = models.DateTimeField()
    delivery_date = models.DateTimeField(blank=True, null=True)
    delivery_address = models.TextField()
    delivery_notes = models.TextField(blank=True, null=True)
    is_delivered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Deliveries"

    def __str__(self):
        return f"Delivery for Order #{self.order.id}"

class Commission(models.Model):
    agent = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'agent'})
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Commission rate in percentage")
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    payment_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commission for {self.agent.username} - Order #{self.order.id}"