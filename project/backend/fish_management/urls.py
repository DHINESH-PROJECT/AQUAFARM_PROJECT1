from django.urls import path
from . import views

urlpatterns = [
    # Home and Auth
    path('', views.home, name='home'),
    path('login/<str:role>/', views.login_page, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
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
    
    # AJAX endpoints for data operations
    path('ajax/delete_feed_plan/<int:plan_id>/', views.delete_feed_plan, name='delete_feed_plan'),
    path('ajax/delete_feeding_log/<int:log_id>/', views.delete_feeding_log, name='delete_feeding_log'),
    path('ajax/update_order_status/<int:order_id>/', views.update_order_status, name='update_order_status'),
]