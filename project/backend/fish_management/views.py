from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count, Sum, Avg, F, Max, Min, FloatField
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import *
import json
from datetime import datetime
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from docx import Document

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4

# Get the User model
User = get_user_model()
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd
from django.db.models import Count, Sum, Avg
from django.utils import timezone

def home(request):
    return render(request, 'home.html')

def login_page(request, role):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user and user.role == role:
            login(request, user)
            return redirect(f'/{role}_dashboard/')
        else:
            return render(request, f'auth/login_{role}.html', {'error': 'Invalid credentials'})
    
    return render(request, f'auth/login_{role}.html')

def register_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        
        if User.objects.filter(username=username).exists():
            return render(request, 'auth/register.html', {'error': 'Username already exists'})
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role,
            phone=phone,
            address=address
        )
        
        login(request, user)
        return redirect(f'/{role}_dashboard/')
    
    return render(request, 'auth/register.html')

@login_required
def farmer_dashboard(request):
    if request.user.role != 'farmer':
        return redirect('home')
    return render(request, 'dashboards/farmer_dashboard.html')

@login_required
def producer_dashboard(request):
    if request.user.role != 'producer':
        return redirect('home')
    return render(request, 'dashboards/producer_dashboard.html')

@login_required
def agent_dashboard(request):
    if request.user.role != 'agent':
        return redirect('home')
    return render(request, 'dashboards/agent_dashboard.html')

@login_required
def species_page(request):
    species_list = Species.objects.all()
    return render(request, 'pages/species.html', {'species_list': species_list})

@login_required
def feed_plans_page(request):
    if request.method == 'POST':
        # Handle new feed plan creation
        species_id = request.POST.get('species_id')
        feed_type = request.POST.get('feed_type')
        quantity_per_day = request.POST.get('quantity_per_day')
        feeding_times = request.POST.get('feeding_times')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        notes = request.POST.get('notes', '')
        
        try:
            species = Species.objects.get(id=species_id)
            # Convert feeding times string to list
            feeding_times_list = [time.strip() for time in feeding_times.split(',')]
            
            FeedPlan.objects.create(
                farmer=request.user,
                species=species,
                feed_type=feed_type,
                quantity_per_day=float(quantity_per_day),
                feeding_times=feeding_times_list,
                start_date=start_date,
                end_date=end_date,
                notes=notes
            )
            messages.success(request, 'Feed plan created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating feed plan: {str(e)}')
        
        return redirect('feed_plans')
    
    if request.user.role == 'farmer':
        feed_plans = FeedPlan.objects.filter(farmer=request.user)
    else:
        feed_plans = FeedPlan.objects.all()
    
    species_list = Species.objects.all()
    return render(request, 'pages/feed_plans.html', {
        'feed_plans': feed_plans,
        'species_list': species_list
    })

@login_required
def feeding_logs_page(request):
    if request.method == 'POST':
        # Handle new feeding log creation
        feed_plan_id = request.POST.get('feed_plan_id')
        feeding_date = request.POST.get('feeding_date')
        feeding_time = request.POST.get('feeding_time')
        quantity_fed = request.POST.get('quantity_fed')
        water_temperature = request.POST.get('water_temperature')
        ph_level = request.POST.get('ph_level')
        mortality_count = request.POST.get('mortality_count', 0)
        notes = request.POST.get('notes', '')
        
        try:
            feed_plan = FeedPlan.objects.get(id=feed_plan_id)
            
            FeedingLog.objects.create(
                feed_plan=feed_plan,
                farmer=request.user,
                feeding_date=feeding_date,
                feeding_time=feeding_time,
                quantity_fed=float(quantity_fed),
                water_temperature=float(water_temperature) if water_temperature else None,
                ph_level=float(ph_level) if ph_level else None,
                mortality_count=int(mortality_count),
                notes=notes
            )
            messages.success(request, 'Feeding log created successfully!')
        except Exception as e:
            messages.error(request, f'Error creating feeding log: {str(e)}')
        
        return redirect('feeding_logs')
    
    # Get feeding logs based on user role
    if request.user.role == 'farmer':
        feeding_logs = FeedingLog.objects.filter(farmer=request.user).order_by('-feeding_date', '-feeding_time')
        feed_plans = FeedPlan.objects.filter(farmer=request.user, is_active=True)
        logs_queryset = FeedingLog.objects.filter(farmer=request.user)
    else:
        feeding_logs = FeedingLog.objects.all().order_by('-feeding_date', '-feeding_time')
        feed_plans = FeedPlan.objects.filter(is_active=True)
        logs_queryset = FeedingLog.objects.all()
    
    # Calculate statistics for the current month
    from datetime import date
    current_month = date.today().replace(day=1)
    
    # Monthly calculations
    monthly_logs = logs_queryset.filter(
        feeding_date__year=current_month.year,
        feeding_date__month=current_month.month
    )
    
    # Calculate totals and averages
    total_logs_month = monthly_logs.count()
    total_feed_used = logs_queryset.aggregate(total=Sum('quantity_fed'))['total'] or 0
    avg_ph_level = logs_queryset.filter(ph_level__isnull=False).aggregate(avg=Avg('ph_level'))['avg']
    if avg_ph_level:
        avg_ph_level = round(avg_ph_level, 2)
    else:
        avg_ph_level = 'N/A'
    total_mortality = logs_queryset.aggregate(total=Sum('mortality_count'))['total'] or 0
    
    return render(request, 'pages/feeding_logs.html', {
        'feeding_logs': feeding_logs,
        'feed_plans': feed_plans,
        'total_logs_month': total_logs_month,
        'total_feed_used': round(total_feed_used, 2),
        'avg_ph_level': avg_ph_level,
        'total_mortality': total_mortality
    })

@login_required
def inventory_page(request):
    if request.method == 'POST':
        # Handle new inventory item creation
        item_name = request.POST.get('item_name')
        item_type = request.POST.get('item_type')
        quantity = request.POST.get('quantity')
        unit = request.POST.get('unit')
        price_per_unit = request.POST.get('price_per_unit')
        minimum_stock = request.POST.get('minimum_stock')
        
        try:
            # Validate data before saving
            if not all([item_name, item_type, quantity, unit, price_per_unit, minimum_stock]):
                messages.error(request, 'All fields are required!')
                return redirect('inventory')
            
            # Check for duplicate items
            if Inventory.objects.filter(
                producer=request.user,
                item_name__iexact=item_name,
                item_type=item_type
            ).exists():
                messages.error(request, f'Item "{item_name}" already exists in {item_type} category!')
                return redirect('inventory')
            
            # Create inventory item
            inventory_item = Inventory.objects.create(
                producer=request.user,
                item_type=item_type,
                item_name=item_name,
                quantity=float(quantity),
                unit=unit,
                price_per_unit=float(price_per_unit),
                minimum_stock=float(minimum_stock)
            )
            
            messages.success(request, f'Inventory item "{item_name}" added successfully!')
        except ValueError as e:
            messages.error(request, 'Please enter valid numeric values for quantity, price, and minimum stock!')
        except Exception as e:
            messages.error(request, f'Error adding inventory item: {str(e)}')
        
        return redirect('inventory')
    
    # Get inventory items based on user role
    if request.user.role == 'producer':
        inventory_items = Inventory.objects.filter(producer=request.user).order_by('-updated_at')
    else:
        inventory_items = Inventory.objects.all().order_by('-updated_at')
    
    # Add calculated total value to each item
    for item in inventory_items:
        item.total_value = item.quantity * float(item.price_per_unit)
    
    # Calculate inventory statistics
    fish_stock = inventory_items.filter(item_type='fish').aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    feed_stock = inventory_items.filter(item_type='feed').aggregate(
        total=Sum('quantity')
    )['total'] or 0
    
    equipment_count = inventory_items.filter(item_type='equipment').count()
    
    # Calculate low stock alerts
    low_stock_items = inventory_items.filter(quantity__lte=models.F('minimum_stock'))
    low_stock_alerts = low_stock_items.count()
    
    # Calculate total inventory value
    total_value = sum(item.quantity * float(item.price_per_unit) for item in inventory_items)
    
    # Calculate items by category
    category_stats = {
        'fish': {
            'count': inventory_items.filter(item_type='fish').count(),
            'total_quantity': fish_stock,
            'total_value': sum(item.quantity * float(item.price_per_unit) 
                             for item in inventory_items.filter(item_type='fish'))
        },
        'feed': {
            'count': inventory_items.filter(item_type='feed').count(),
            'total_quantity': feed_stock,
            'total_value': sum(item.quantity * float(item.price_per_unit) 
                             for item in inventory_items.filter(item_type='feed'))
        },
        'equipment': {
            'count': equipment_count,
            'total_quantity': inventory_items.filter(item_type='equipment').aggregate(
                total=Sum('quantity')
            )['total'] or 0,
            'total_value': sum(item.quantity * float(item.price_per_unit) 
                             for item in inventory_items.filter(item_type='equipment'))
        }
    }
    
    # Get recent orders affecting inventory
    recent_orders = Order.objects.filter(
        inventory_item__in=inventory_items
    ).order_by('-order_date')[:10]
    
    # Calculate order statistics
    pending_orders = Order.objects.filter(
        inventory_item__in=inventory_items,
        status='pending'
    ).count()
    
    shipped_orders = Order.objects.filter(
        inventory_item__in=inventory_items,
        status='shipped'
    ).count()
    
    return render(request, 'pages/inventory.html', {
        'inventory_items': inventory_items,
        'fish_stock': round(fish_stock, 2),
        'feed_stock': round(feed_stock, 2),
        'equipment_count': equipment_count,
        'low_stock_alerts': low_stock_alerts,
        'low_stock_items': low_stock_items,
        'total_value': round(total_value, 2),
        'category_stats': category_stats,
        'recent_orders': recent_orders,
        'pending_orders': pending_orders,
        'shipped_orders': shipped_orders
    })

@login_required
def orders_page(request):
    if request.method == 'POST':
        # Handle new order creation
        inventory_item_id = request.POST.get('inventory_item_id')
        quantity = request.POST.get('quantity')
        
        try:
            inventory_item = Inventory.objects.get(id=inventory_item_id)
            total_price = float(quantity) * float(inventory_item.price_per_unit)
            
            Order.objects.create(
                customer=request.user,
                producer=inventory_item.producer,
                inventory_item=inventory_item,
                quantity=float(quantity),
                total_price=total_price
            )
            messages.success(request, 'Order placed successfully!')
        except Exception as e:
            messages.error(request, f'Error placing order: {str(e)}')
        
        return redirect('orders')
    
    # Get orders based on user role
    if request.user.role == 'producer':
        orders = Order.objects.filter(producer=request.user).select_related('customer', 'producer', 'inventory_item').order_by('-order_date')
    elif request.user.role == 'farmer':
        orders = Order.objects.filter(customer=request.user).select_related('customer', 'producer', 'inventory_item').order_by('-order_date')
    else:
        orders = Order.objects.all().select_related('customer', 'producer', 'inventory_item').order_by('-order_date')
    
    # Calculate comprehensive order statistics
    order_stats = orders.aggregate(
        total_orders=Count('id'),
        total_revenue=Sum('total_price') or 0,
        average_order_value=Avg('total_price') or 0,
        total_quantity=Sum('quantity') or 0,
        max_order_value=Max('total_price') or 0,
        min_order_value=Min('total_price') or 0
    )
    
    # Calculate status-wise breakdowns
    status_breakdown = orders.values('status').annotate(
        count=Count('id'),
        total_value=Sum('total_price'),
        avg_value=Avg('total_price'),
        total_qty=Sum('quantity')
    ).order_by('status')
    
    # Calculate item-wise statistics
    item_stats = orders.values('inventory_item__item_name', 'inventory_item__unit').annotate(
        order_count=Count('id'),
        total_quantity=Sum('quantity'),
        total_value=Sum('total_price'),
        avg_price_per_unit=Avg('inventory_item__price_per_unit', output_field=FloatField())
    ).order_by('-total_value')[:10]  # Top 10 items by value
    
    # Calculate customer statistics
    customer_stats = orders.values('customer__username', 'customer__role').annotate(
        order_count=Count('id'),
        total_spent=Sum('total_price'),
        avg_order_value=Avg('total_price'),
        last_order_date=Max('order_date')
    ).order_by('-total_spent')[:10]  # Top 10 customers by spending
    
    # Calculate monthly revenue trend (last 6 months)
    from datetime import datetime, timedelta
    from django.db.models import Q
    from django.db.models.functions import TruncMonth
    
    monthly_stats = orders.filter(
        order_date__gte=datetime.now() - timedelta(days=180)
    ).annotate(
        month=TruncMonth('order_date')
    ).values('month').annotate(
        order_count=Count('id'),
        revenue=Sum('total_price'),
        avg_order_value=Avg('total_price')
    ).order_by('month')
    
    # Get specific status counts for dashboard cards
    pending_orders = orders.filter(status='pending').count()
    approved_orders = orders.filter(status='approved').count()
    shipped_orders = orders.filter(status='shipped').count()
    delivered_orders = orders.filter(status='delivered').count()
    rejected_orders = orders.filter(status='rejected').count()
    
    # Calculate additional metrics
    completion_rate = (delivered_orders / max(order_stats['total_orders'], 1)) * 100
    approval_rate = (approved_orders / max(pending_orders + approved_orders + rejected_orders, 1)) * 100
    
    # Get inventory items for order creation
    inventory_items = Inventory.objects.all().order_by('item_name')
    
    return render(request, 'pages/orders.html', {
        'orders': orders,
        'inventory_items': inventory_items,
        # Order statistics
        'order_stats': order_stats,
        'status_breakdown': status_breakdown,
        'item_stats': item_stats,
        'customer_stats': customer_stats,
        'monthly_stats': monthly_stats,
        # Dashboard metrics
        'pending_orders': pending_orders,
        'approved_orders': approved_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        'rejected_orders': rejected_orders,
        'total_revenue': order_stats['total_revenue'],
        'completion_rate': round(completion_rate, 1),
        'approval_rate': round(approval_rate, 1),
        'average_order_value': round(order_stats['average_order_value'], 2),
        'total_quantity': order_stats['total_quantity']
    })

@login_required
def delivery_page(request):
    if request.method == 'POST':
        # Handle delivery assignment
        order_id = request.POST.get('order_id')
        agent_id = request.POST.get('agent_id')
        worker_id = request.POST.get('worker_id')
        pickup_date = request.POST.get('pickup_date')
        delivery_address = request.POST.get('delivery_address')
        delivery_notes = request.POST.get('delivery_notes', '')
        
        try:
            # Get the order
            order = Order.objects.get(id=order_id)
            
            # Check if delivery already exists for this order
            if Delivery.objects.filter(order=order).exists():
                messages.error(request, f'Delivery already assigned for Order #{order.id}')
                return redirect('delivery')
            
            # Get agent and worker
            agent = User.objects.get(id=agent_id, role='agent')
            worker = User.objects.get(id=worker_id, role='worker')
            
            # Create delivery
            delivery = Delivery.objects.create(
                order=order,
                agent=agent,
                worker=worker,
                pickup_date=pickup_date,
                delivery_address=delivery_address,
                delivery_notes=delivery_notes
            )
            
            # Update order status to shipped
            order.status = 'shipped'
            order.save()
            
            messages.success(request, f'Delivery assigned successfully! Delivery ID: #DEL-{delivery.id:03d}')
        except Order.DoesNotExist:
            messages.error(request, 'Selected order not found!')
        except User.DoesNotExist:
            messages.error(request, 'Selected agent or worker not found!')
        except Exception as e:
            messages.error(request, f'Error assigning delivery: {str(e)}')
        
        return redirect('delivery')
    
    # Get deliveries with related data
    deliveries = Delivery.objects.select_related(
        'order', 'agent', 'worker', 'order__producer', 'order__customer', 'order__inventory_item'
    ).all().order_by('-created_at')
    
    # Calculate statistics
    pending_count = deliveries.filter(is_delivered=False).count()
    delivered_today_count = deliveries.filter(
        is_delivered=True, 
        delivery_date__date=timezone.now().date()
    ).count()
    
    # Count deliveries that are shipped but not delivered as in transit
    in_transit_count = deliveries.filter(
        is_delivered=False,
        order__status='shipped'
    ).count()
    
    active_workers_count = User.objects.filter(role='worker', is_active=True).count()
    
    # Get available orders for assignment (approved but not yet assigned to delivery)
    assigned_order_ids = Delivery.objects.values_list('order_id', flat=True)
    available_orders = Order.objects.filter(
        status='approved'
    ).exclude(id__in=assigned_order_ids).select_related(
        'customer', 'producer', 'inventory_item'
    )
    
    # Get available agents and workers
    available_agents = User.objects.filter(role='agent', is_active=True)
    available_workers = User.objects.filter(role='worker', is_active=True)
    
    context = {
        'deliveries': deliveries,
        'pending_count': pending_count,
        'in_transit_count': in_transit_count,
        'delivered_today_count': delivered_today_count,
        'active_workers_count': active_workers_count,
        'available_orders': available_orders,
        'available_agents': available_agents,
        'available_workers': available_workers,
    }
    return render(request, 'pages/delivery.html', context)



@login_required
def commission_page(request):
    """Commission page with delivery-based calculations"""
    
    # Get commissions based on user role
    if request.user.role == 'agent':
        commissions = Commission.objects.filter(agent=request.user).select_related(
            'order', 'order__customer', 'order__producer', 'order__inventory_item'
        ).order_by('-created_at')
        # Get deliveries for this agent
        deliveries = Delivery.objects.filter(agent=request.user).select_related(
            'order', 'order__customer', 'order__producer', 'order__inventory_item'
        )
    else:
        commissions = Commission.objects.all().select_related(
            'agent', 'order', 'order__customer', 'order__producer', 'order__inventory_item'
        ).order_by('-created_at')
        deliveries = Delivery.objects.all().select_related(
            'agent', 'order', 'order__customer', 'order__producer', 'order__inventory_item'
        )
    
    # Calculate delivery-based commission statistics
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Get delivered orders for commission calculation
    delivered_orders = deliveries.filter(is_delivered=True)
    
    # Calculate automatic commissions for delivered orders that don't have commission records
    commission_rate = 5.0  # Default 5% commission rate
    
    for delivery in delivered_orders:
        # Check if commission already exists for this order
        existing_commission = commissions.filter(order=delivery.order).first()
        if not existing_commission:
            # Create commission for delivered order
            commission_amount = (float(delivery.order.total_price) * commission_rate) / 100
            Commission.objects.create(
                agent=delivery.agent,
                order=delivery.order,
                commission_rate=commission_rate,
                commission_amount=commission_amount,
                is_paid=False
            )
    
    # Refresh commissions after auto-creation
    if request.user.role == 'agent':
        commissions = Commission.objects.filter(agent=request.user).select_related(
            'order', 'order__customer', 'order__producer', 'order__inventory_item'
        ).order_by('-created_at')
    else:
        commissions = Commission.objects.all().select_related(
            'agent', 'order', 'order__customer', 'order__producer', 'order__inventory_item'
        ).order_by('-created_at')
    
    # Calculate comprehensive statistics
    total_earnings = commissions.filter(is_paid=True).aggregate(
        total=Sum('commission_amount')
    )['total'] or 0
    
    pending_commission = commissions.filter(is_paid=False).aggregate(
        total=Sum('commission_amount')
    )['total'] or 0
    
    paid_this_month = commissions.filter(
        is_paid=True,
        payment_date__gte=current_month
    ).aggregate(total=Sum('commission_amount'))['total'] or 0
    
    avg_commission = commissions.aggregate(
        avg=Avg('commission_rate')
    )['avg'] or 0
    
    # Calculate delivery-based metrics
    completed_deliveries = delivered_orders.count()
    monthly_deliveries = delivered_orders.filter(
        delivery_date__gte=current_month
    ).count()
    
    monthly_commission_earned = commissions.filter(
        created_at__gte=current_month
    ).aggregate(total=Sum('commission_amount'))['total'] or 0
    
    # Get top customers by commission generated
    top_customers = commissions.values('order__customer__username').annotate(
        total_commission=Sum('commission_amount'),
        delivery_count=Count('order')
    ).order_by('-total_commission')[:5]
    
    # Calculate performance metrics
    total_deliveries = deliveries.count()
    on_time_deliveries = deliveries.filter(
        delivery_date__lte=F('pickup_date') + timedelta(days=1)
    ).count()
    
    on_time_percentage = (on_time_deliveries / max(total_deliveries, 1)) * 100
    
    return render(request, 'pages/commission.html', {
        'commissions': commissions,
        'deliveries': deliveries,
        'total_earnings': total_earnings,
        'pending_commission': pending_commission,
        'paid_this_month': paid_this_month,
        'avg_commission': avg_commission,
        'deliveries_completed': completed_deliveries,
        'monthly_orders_delivered': monthly_deliveries,
        'monthly_commission_earned': monthly_commission_earned,
        'top_customers': top_customers,
        'on_time_percentage': on_time_percentage,
        'commission_rate': commission_rate
    })

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

# API Views
@api_view(['GET'])
@login_required
def api_feeding_stats(request):
    """API endpoint to get feeding log statistics"""
    if request.user.role == 'farmer':
        logs_queryset = FeedingLog.objects.filter(farmer=request.user)
    else:
        logs_queryset = FeedingLog.objects.all()
    
    # Get filter parameters
    date_filter = request.GET.get('date')
    plan_filter = request.GET.get('plan_id')
    
    if date_filter:
        logs_queryset = logs_queryset.filter(feeding_date=date_filter)
    
    if plan_filter:
        logs_queryset = logs_queryset.filter(feed_plan_id=plan_filter)
    
    # Calculate statistics
    total_logs = logs_queryset.count()
    total_feed = logs_queryset.aggregate(total=Sum('quantity_fed'))['total'] or 0
    total_mortality = logs_queryset.aggregate(total=Sum('mortality_count'))['total'] or 0
    avg_ph = logs_queryset.filter(ph_level__isnull=False).aggregate(avg=Avg('ph_level'))['avg']
    avg_temp = logs_queryset.filter(water_temperature__isnull=False).aggregate(avg=Avg('water_temperature'))['avg']
    
    # Calculate feed efficiency (simplified metric)
    feed_efficiency = 100 if total_mortality == 0 else max(0, 100 - (total_mortality * 5))
    
    # Calculate daily average
    unique_dates = logs_queryset.values_list('feeding_date', flat=True).distinct().count()
    daily_average = total_feed / unique_dates if unique_dates > 0 else 0
    
    return Response({
        'total_logs': total_logs,
        'total_feed_used': round(total_feed, 2),
        'total_mortality': total_mortality,
        'avg_ph_level': round(avg_ph, 2) if avg_ph else None,
        'avg_water_temp': round(avg_temp, 1) if avg_temp else None,
        'feed_efficiency': round(feed_efficiency, 1),
        'daily_average': round(daily_average, 2)
    })

@api_view(['GET'])
@login_required
def api_inventory_stats(request):
    """API endpoint to get inventory statistics"""
    if request.user.role == 'producer':
        inventory_items = Inventory.objects.filter(producer=request.user)
    else:
        inventory_items = Inventory.objects.all()
    
    # Get filter parameters
    category_filter = request.GET.get('category')
    status_filter = request.GET.get('status')
    
    if category_filter:
        inventory_items = inventory_items.filter(item_type=category_filter)
    
    if status_filter == 'low-stock':
        inventory_items = inventory_items.filter(quantity__lte=F('minimum_stock'))
    elif status_filter == 'in-stock':
        inventory_items = inventory_items.filter(quantity__gt=F('minimum_stock'))
    
    # Calculate statistics
    fish_stock = inventory_items.filter(item_type='fish').aggregate(total=Sum('quantity'))['total'] or 0
    feed_stock = inventory_items.filter(item_type='feed').aggregate(total=Sum('quantity'))['total'] or 0
    equipment_count = inventory_items.filter(item_type='equipment').count()
    low_stock_count = inventory_items.filter(quantity__lte=F('minimum_stock')).count()
    
    # Calculate total value
    total_value = sum(item.quantity * float(item.price_per_unit) for item in inventory_items)
    
    # Category breakdown
    categories = {}
    for item_type in ['fish', 'feed', 'equipment']:
        category_items = inventory_items.filter(item_type=item_type)
        categories[item_type] = {
            'count': category_items.count(),
            'total_quantity': category_items.aggregate(total=Sum('quantity'))['total'] or 0,
            'total_value': sum(item.quantity * float(item.price_per_unit) for item in category_items)
        }
    
    return Response({
        'fish_stock': round(fish_stock, 2),
        'feed_stock': round(feed_stock, 2),
        'equipment_count': equipment_count,
        'low_stock_count': low_stock_count,
        'total_value': round(total_value, 2),
        'total_items': inventory_items.count(),
        'categories': categories
    })

@api_view(['POST'])
@login_required
def api_update_stock(request):
    """API endpoint to update inventory stock"""
    try:
        item_id = request.data.get('item_id')
        action = request.data.get('action')  # 'add' or 'remove'
        quantity = float(request.data.get('quantity', 0))
        
        if not all([item_id, action, quantity > 0]):
            return Response({'error': 'Missing required parameters'}, status=400)
        
        # Get inventory item
        if request.user.role == 'producer':
            inventory_item = Inventory.objects.get(id=item_id, producer=request.user)
        else:
            inventory_item = Inventory.objects.get(id=item_id)
        
        # Update stock
        if action == 'add':
            inventory_item.quantity += quantity
        elif action == 'remove':
            if inventory_item.quantity >= quantity:
                inventory_item.quantity -= quantity
            else:
                return Response({'error': 'Insufficient stock to remove'}, status=400)
        else:
            return Response({'error': 'Invalid action'}, status=400)
        
        inventory_item.save()
        
        return Response({
            'success': True,
            'message': f'Stock {action}ed successfully',
            'new_quantity': inventory_item.quantity,
            'status': 'low-stock' if inventory_item.quantity <= inventory_item.minimum_stock else 'in-stock'
        })
        
    except Inventory.DoesNotExist:
        return Response({'error': 'Inventory item not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['DELETE'])
@login_required  
def api_delete_inventory_item(request, item_id):
    """API endpoint to delete inventory item"""
    try:
        if request.user.role == 'producer':
            inventory_item = Inventory.objects.get(id=item_id, producer=request.user)
        else:
            inventory_item = Inventory.objects.get(id=item_id)
        
        # Check if item has pending orders
        pending_orders = Order.objects.filter(
            inventory_item=inventory_item,
            status__in=['pending', 'approved', 'shipped']
        ).count()
        
        if pending_orders > 0:
            return Response({
                'error': f'Cannot delete item. There are {pending_orders} pending orders for this item.'
            }, status=400)
        
        item_name = inventory_item.item_name
        inventory_item.delete()
        
        return Response({
            'success': True,
            'message': f'Item "{item_name}" deleted successfully'
        })
        
    except Inventory.DoesNotExist:
        return Response({'error': 'Inventory item not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def api_species(request):
    species = Species.objects.all()
    data = [{
        'id': s.id,
        'name': s.name,
        'scientific_name': s.scientific_name,
        'description': s.description,
        'image': s.image.url if s.image else None,
        'optimal_temp': s.optimal_temp,
        'ph_range': s.ph_range,
        'feeding_frequency': s.feeding_frequency
    } for s in species]
    return Response(data)

@api_view(['GET', 'POST'])
def api_feed_plans(request):
    if request.method == 'GET':
        plans = FeedPlan.objects.filter(farmer=request.user)
        data = [{
            'id': p.id,
            'species': p.species.name,
            'feed_type': p.feed_type,
            'quantity_per_day': p.quantity_per_day,
            'start_date': p.start_date,
            'end_date': p.end_date,
            'is_active': p.is_active
        } for p in plans]
        return Response(data)
    
    elif request.method == 'POST':
        data = request.data
        plan = FeedPlan.objects.create(
            farmer=request.user,
            species_id=data['species_id'],
            feed_type=data['feed_type'],
            quantity_per_day=data['quantity_per_day'],
            feeding_times=data['feeding_times'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            notes=data.get('notes', '')
        )
        return Response({'id': plan.id, 'message': 'Feed plan created successfully'})

# AJAX Views for data operations
@login_required
def delete_feed_plan(request, plan_id):
    if request.method == 'POST':
        try:
            plan = FeedPlan.objects.get(id=plan_id, farmer=request.user)
            plan.delete()
            return JsonResponse({'success': True, 'message': 'Feed plan deleted successfully'})
        except FeedPlan.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Feed plan not found'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def delete_feeding_log(request, log_id):
    if request.method == 'POST':
        try:
            log = FeedingLog.objects.get(id=log_id, farmer=request.user)
            log.delete()
            return JsonResponse({'success': True, 'message': 'Feeding log deleted successfully'})
        except FeedingLog.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Feeding log not found'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def update_order_status(request, order_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            
            order = Order.objects.get(id=order_id)
            order.status = new_status
            order.save()
            
            return JsonResponse({'success': True, 'message': f'Order status updated to {new_status}'})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def commission_page(request):
    commissions = Commission.objects.select_related('order__customer').all()
    total_earnings = commissions.aggregate(total=Sum('commission_amount'))['total'] or 0
    pending_commission = commissions.filter(is_paid=False).aggregate(total=Sum('commission_amount'))['total'] or 0
    paid_this_month = commissions.filter(
        is_paid=True,
        payment_date__month=timezone.now().month,
        payment_date__year=timezone.now().year
    ).aggregate(total=Sum('commission_amount'))['total'] or 0
    avg_commission = commissions.aggregate(avg=Avg('commission_rate'))['avg'] or 0

    deliveries_completed = Delivery.objects.filter(is_delivered=True).count()

    # Monthly summary
    now = timezone.now()
    monthly_orders_delivered = Delivery.objects.filter(
        is_delivered=True,
        delivery_date__month=now.month,
        delivery_date__year=now.year
    ).count()
    monthly_commission_earned = commissions.filter(
        is_paid=True,
        payment_date__month=now.month,
        payment_date__year=now.year
    ).aggregate(total=Sum('commission_amount'))['total'] or 0

    context = {
        'commissions': commissions,
        'total_earnings': total_earnings,
        'pending_commission': pending_commission,
        'paid_this_month': paid_this_month,
        'avg_commission': avg_commission,
        'deliveries_completed': deliveries_completed,
        'monthly_orders_delivered': monthly_orders_delivered,
        'monthly_commission_earned': monthly_commission_earned,
        'deliveries': Delivery.objects.select_related('order__customer', 'order__inventory_item').all(),
        'commission_rate': 5.0,  # Fixed 5% commission rate
    }
    return render(request, 'pages/commission.html', context)

@api_view(['POST'])
@login_required
def api_update_delivery_status(request):
    """API endpoint to update delivery status"""
    try:
        delivery_id = request.data.get('delivery_id')
        action = request.data.get('action')  # 'mark_delivered', 'update_notes'
        
        delivery = Delivery.objects.get(id=delivery_id)
        
        if action == 'mark_delivered':
            if delivery.is_delivered:
                return Response({'error': 'Delivery already marked as delivered'}, status=400)
            
            delivery.is_delivered = True
            delivery.delivery_date = timezone.now()
            delivery.order.status = 'delivered'
            delivery.order.save()
            delivery.save()
            
            return Response({
                'success': True,
                'message': 'Delivery marked as completed successfully',
                'delivery_date': delivery.delivery_date.strftime('%Y-%m-%d %H:%M')
            })
        
        elif action == 'update_notes':
            notes = request.data.get('notes', '')
            delivery.delivery_notes = notes
            delivery.save()
            
            return Response({
                'success': True,
                'message': 'Delivery notes updated successfully'
            })
        
        else:
            return Response({'error': 'Invalid action'}, status=400)
            
    except Delivery.DoesNotExist:
        return Response({'error': 'Delivery not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@login_required
def api_delivery_stats(request):
    """API endpoint to get delivery statistics"""
    try:
        deliveries = Delivery.objects.all()
        
        # Filter parameters
        status_filter = request.GET.get('status')
        date_filter = request.GET.get('date')
        
        if status_filter == 'pending':
            deliveries = deliveries.filter(is_delivered=False)
        elif status_filter == 'delivered':
            deliveries = deliveries.filter(is_delivered=True)
        elif status_filter == 'in_transit':
            deliveries = deliveries.filter(is_delivered=False, order__status='shipped')
        
        if date_filter:
            deliveries = deliveries.filter(pickup_date__date=date_filter)
        
        # Calculate statistics
        total_deliveries = deliveries.count()
        pending_count = deliveries.filter(is_delivered=False).count()
        delivered_count = deliveries.filter(is_delivered=True).count()
        delivered_today = deliveries.filter(
            is_delivered=True,
            delivery_date__date=timezone.now().date()
        ).count()
        
        # Agent and worker statistics
        active_agents = User.objects.filter(role='agent', is_active=True).count()
        active_workers = User.objects.filter(role='worker', is_active=True).count()
        
        # Average delivery time (for completed deliveries)
        completed_deliveries = deliveries.filter(is_delivered=True)
        avg_delivery_hours = 0
        
        if completed_deliveries.exists():
            total_hours = 0
            count = 0
            for delivery in completed_deliveries:
                if delivery.delivery_date and delivery.pickup_date:
                    diff = delivery.delivery_date - delivery.pickup_date
                    total_hours += diff.total_seconds() / 3600
                    count += 1
            
            if count > 0:
                avg_delivery_hours = round(total_hours / count, 1)
        
        return Response({
            'total_deliveries': total_deliveries,
            'pending_count': pending_count,
            'delivered_count': delivered_count,
            'delivered_today': delivered_today,
            'active_agents': active_agents,
            'active_workers': active_workers,
            'avg_delivery_hours': avg_delivery_hours
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@login_required
@csrf_exempt
def approve_order(request, order_id):
    """Approve an order"""
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            
            # Check permission - only producers can approve their own orders, or admin users
            if request.user.role == 'producer' and order.producer != request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'You can only approve your own orders.'
                }, status=403)
            
            # Check if order is in pending status
            if order.status != 'pending':
                return JsonResponse({
                    'success': False,
                    'message': f'Order is already {order.status}. Only pending orders can be approved.'
                }, status=400)
            
            # Check inventory availability
            if order.inventory_item.quantity < order.quantity:
                return JsonResponse({
                    'success': False,
                    'message': f'Insufficient stock. Available: {order.inventory_item.quantity}, Required: {order.quantity}'
                }, status=400)
            
            # Update order status
            order.status = 'approved'
            order.save()
            
            # Update inventory stock
            order.inventory_item.quantity -= order.quantity
            order.inventory_item.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Order #{order.id} approved successfully!',
                'new_status': 'approved'
            })
            
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Order not found.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error approving order: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@login_required
@csrf_exempt
def reject_order(request, order_id):
    """Reject an order"""
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            
            # Check permission - only producers can reject their own orders, or admin users
            if request.user.role == 'producer' and order.producer != request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'You can only reject your own orders.'
                }, status=403)
            
            # Check if order can be rejected
            if order.status in ['shipped', 'delivered']:
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot reject order that is already {order.status}.'
                }, status=400)
            
            # Update order status
            old_status = order.status
            order.status = 'rejected'
            order.save()
            
            # If order was previously approved, return stock to inventory
            if old_status == 'approved':
                order.inventory_item.quantity += order.quantity
                order.inventory_item.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Order #{order.id} rejected successfully!',
                'new_status': 'rejected'
            })
            
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Order not found.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error rejecting order: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@login_required
@csrf_exempt
def ship_order(request, order_id):
    """Mark order as shipped"""
    if request.method == 'POST':
        try:
            order = Order.objects.get(id=order_id)
            
            # Check permission - only producers can ship their own orders, or admin users
            if request.user.role == 'producer' and order.producer != request.user:
                return JsonResponse({
                    'success': False,
                    'message': 'You can only ship your own orders.'
                }, status=403)
            
            # Check if order is approved
            if order.status != 'approved':
                return JsonResponse({
                    'success': False,
                    'message': 'Only approved orders can be shipped.'
                }, status=400)
            
            # Update order status
            order.status = 'shipped'
            order.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Order #{order.id} marked as shipped!',
                'new_status': 'shipped'
            })
            
        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Order not found.'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error shipping order: {str(e)}'
            }, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)

@csrf_exempt
def recalculate_commissions(request):
    """AJAX endpoint to recalculate commissions based on completed deliveries"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        # Get all delivered orders that don't have commission records
        delivered_orders = Order.objects.filter(
            status='delivered'
        ).exclude(
            commission__isnull=False
        )
        
        # Create commission records for delivered orders
        commissions_created = 0
        for order in delivered_orders:
            # Calculate commission (5% of order total)
            commission_rate = 5.0
            commission_amount = (order.total_price * commission_rate) / 100
            
            # Create commission record
            Commission.objects.create(
                agent=order.customer,  # Assuming agent is the customer
                order=order,
                commission_rate=commission_rate,
                commission_amount=commission_amount,
                is_paid=False
            )
            commissions_created += 1
        
        # Also update existing commission amounts if needed
        existing_commissions = Commission.objects.filter(order__status='delivered')
        for commission in existing_commissions:
            expected_amount = (commission.order.total_price * commission.commission_rate) / 100
            if commission.commission_amount != expected_amount:
                commission.commission_amount = expected_amount
                commission.save()
        
        return JsonResponse({
            'success': True, 
            'message': f'Created {commissions_created} new commission records',
            'commissions_created': commissions_created
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})