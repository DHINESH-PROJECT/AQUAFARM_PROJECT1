from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q, Count
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
    
    if request.user.role == 'farmer':
        feeding_logs = FeedingLog.objects.filter(farmer=request.user)
        feed_plans = FeedPlan.objects.filter(farmer=request.user, is_active=True)
    else:
        feeding_logs = FeedingLog.objects.all()
        feed_plans = FeedPlan.objects.filter(is_active=True)
    
    return render(request, 'pages/feeding_logs.html', {
        'feeding_logs': feeding_logs,
        'feed_plans': feed_plans
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
            Inventory.objects.create(
                producer=request.user,
                item_type=item_type,
                item_name=item_name,
                quantity=float(quantity),
                unit=unit,
                price_per_unit=float(price_per_unit),
                minimum_stock=float(minimum_stock)
            )
            messages.success(request, 'Inventory item added successfully!')
        except Exception as e:
            messages.error(request, f'Error adding inventory item: {str(e)}')
        
        return redirect('inventory')
    
    if request.user.role == 'producer':
        inventory_items = Inventory.objects.filter(producer=request.user)
    else:
        inventory_items = Inventory.objects.all()
    return render(request, 'pages/inventory.html', {'inventory_items': inventory_items})

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
    
    if request.user.role == 'producer':
        orders = Order.objects.filter(producer=request.user)
    elif request.user.role == 'farmer':
        orders = Order.objects.filter(customer=request.user)
    else:
        orders = Order.objects.all()
    
    # Get inventory items for order creation
    inventory_items = Inventory.objects.all()
    return render(request, 'pages/orders.html', {
        'orders': orders,
        'inventory_items': inventory_items
    })

@login_required
def delivery_page(request):
    deliveries = Delivery.objects.select_related('order', 'agent', 'worker', 'order__producer', 'order__customer').all()
    pending_count = deliveries.filter(is_delivered=False).count()
    delivered_today_count = deliveries.filter(is_delivered=True, delivery_date__date=timezone.now().date()).count()
    # In Transit: Only possible if you add a status field, otherwise skip or set to 0

    in_transit_count = 0
    User = get_user_model()
    active_workers_count = User.objects.filter(role='worker', is_active=True).count()

    context = {
        'deliveries': deliveries,
        'pending_count': pending_count,
        'in_transit_count': in_transit_count,
        'delivered_today_count': delivered_today_count,
        'active_workers_count': active_workers_count,
    }
    return render(request, 'pages/delivery.html', context)



@login_required
def commission_page(request):
    if request.user.role == 'agent':
        commissions = Commission.objects.filter(agent=request.user)
    else:
        commissions = Commission.objects.all()
    return render(request, 'pages/commission.html', {'commissions': commissions})

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

# API Views
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
    }
    return render(request, 'pages/commission.html', context)