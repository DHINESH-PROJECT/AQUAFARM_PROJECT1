from django.contrib import admin
from .models import *

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('username', 'email')

@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    list_display = ('name', 'scientific_name', 'optimal_temp', 'feeding_frequency')
    search_fields = ('name', 'scientific_name')

@admin.register(FeedPlan)
class FeedPlanAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'species', 'feed_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'created_at', 'species')
    search_fields = ('farmer__username', 'species__name')

@admin.register(FeedingLog)
class FeedingLogAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'feeding_date', 'feeding_time', 'quantity_fed')
    list_filter = ('feeding_date', 'farmer')
    search_fields = ('farmer__username',)

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'item_type', 'quantity', 'unit', 'producer')
    list_filter = ('item_type', 'producer')
    search_fields = ('item_name',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'producer', 'status', 'total_price', 'order_date')
    list_filter = ('status', 'order_date')
    search_fields = ('customer__username', 'producer__username')

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ('order', 'agent', 'worker', 'pickup_date', 'is_delivered')
    list_filter = ('is_delivered', 'pickup_date')

@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('agent', 'order', 'commission_amount', 'is_paid')
    list_filter = ('is_paid', 'created_at')