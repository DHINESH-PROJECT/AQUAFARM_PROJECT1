from django.urls import path
from . import views

urlpatterns = [
    # Home and Auth
    path('', views.home, name='home'),
    path('login/<str:role>/', views.login_page, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Register
    path('register/', views.register_page, name='register'),
    
    # Dashboards
    path('farmer_dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('producer_dashboard/', views.producer_dashboard, name='producer_dashboard'),
    path('agent_dashboard/', views.agent_dashboard, name='agent_dashboard'),
    
    # Pages
    path('species/', views.species_page, name='species'),
    path('feed_plans/', views.feed_plans_page, name='feed_plans'),
    path('feeding_logs/', views.feeding_logs_page, name='feeding_logs'),
    path('inventory/', views.inventory_page, name='inventory'),
    path('orders/', views.orders_page, name='orders'),
    path('delivery/', views.delivery_page, name='delivery'),
    path('commission/', views.commission_page, name='commission'),
    
    
    # API
    path('api/species/', views.api_species, name='api_species'),
    path('api/feed_plans/', views.api_feed_plans, name='api_feed_plans'),
    path('api/feeding_stats/', views.api_feeding_stats, name='api_feeding_stats'),
    path('api/inventory_stats/', views.api_inventory_stats, name='api_inventory_stats'),
    path('api/update_stock/', views.api_update_stock, name='api_update_stock'),
    path('api/delete_inventory/<int:item_id>/', views.api_delete_inventory_item, name='api_delete_inventory_item'),
    path('api/update_delivery_status/', views.api_update_delivery_status, name='api_update_delivery_status'),
    path('api/delivery_stats/', views.api_delivery_stats, name='api_delivery_stats'),
    
    # AJAX endpoints for data operations
    path('ajax/delete_feed_plan/<int:plan_id>/', views.delete_feed_plan, name='delete_feed_plan'),
    path('ajax/delete_feeding_log/<int:log_id>/', views.delete_feeding_log, name='delete_feeding_log'),
    path('ajax/update_order_status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('ajax/approve_order/<int:order_id>/', views.approve_order, name='approve_order'),
    path('ajax/reject_order/<int:order_id>/', views.reject_order, name='reject_order'),
    path('ajax/ship_order/<int:order_id>/', views.ship_order, name='ship_order'),
    path('ajax/recalculate_commissions/', views.recalculate_commissions, name='recalculate_commissions'),
]