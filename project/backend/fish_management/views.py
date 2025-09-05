from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

# AJAX endpoint to approve an order
@login_required
@require_POST
@csrf_exempt
def ajax_approve_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        if order.status == 'pending':
            order.status = 'approved'
            order.save()
            return JsonResponse({'success': True, 'message': 'Order approved successfully.'})
        else:
            return JsonResponse({'success': False, 'message': 'Order is not pending.'})
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found.'})
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import *
import json
from datetime import datetime
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from docx import Document

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

    # Calculate summary values
    from django.utils import timezone
    now = timezone.now()
    month_logs = feeding_logs.filter(feeding_date__month=now.month, feeding_date__year=now.year)
    total_logs_month = month_logs.count()
    total_feed_used = sum(log.quantity_fed for log in feeding_logs)
    avg_ph_level = round(sum(log.ph_level for log in feeding_logs if log.ph_level is not None) / max(1, sum(1 for log in feeding_logs if log.ph_level is not None)), 2) if feeding_logs else 0
    total_mortality = sum(log.mortality_count for log in feeding_logs)

    return render(request, 'pages/feeding_logs.html', {
        'feeding_logs': feeding_logs,
        'feed_plans': feed_plans,
        'total_logs_month': total_logs_month,
        'total_feed_used': total_feed_used,
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

    # Calculate summary values for dashboard cards
    fish_stock = sum(item.quantity for item in inventory_items if item.item_type == 'fish')
    feed_stock = sum(item.quantity for item in inventory_items if item.item_type == 'feed')
    equipment_count = sum(1 for item in inventory_items if item.item_type == 'equipment')
    low_stock_alerts = sum(1 for item in inventory_items if item.quantity <= item.minimum_stock)

    return render(request, 'pages/inventory.html', {
        'inventory_items': inventory_items,
        'fish_stock': fish_stock,
        'feed_stock': feed_stock,
        'equipment_count': equipment_count,
        'low_stock_alerts': low_stock_alerts
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
    
    if request.user.role == 'producer':
        orders = Order.objects.filter(producer=request.user)
    elif request.user.role == 'farmer':
        orders = Order.objects.filter(customer=request.user)
    else:
        orders = Order.objects.all()
    
    # Get inventory items for order creation
    inventory_items = Inventory.objects.all()

    # Calculate summary values for dashboard cards
    pending_orders = orders.filter(status='pending').count()
    approved_orders = orders.filter(status='approved').count()
    shipped_orders = orders.filter(status='shipped').count()
    total_revenue = sum(order.total_price for order in orders if order.status in ['approved', 'shipped', 'delivered'])

    return render(request, 'pages/orders.html', {
        'orders': orders,
        'inventory_items': inventory_items,
        'pending_orders': pending_orders,
        'approved_orders': approved_orders,
        'shipped_orders': shipped_orders,
        'total_revenue': total_revenue
    })

@login_required
def delivery_page(request):
    deliveries = Delivery.objects.all()
    return render(request, 'pages/delivery.html', {'deliveries': deliveries})

@login_required
def reports_page(request):
    return render(request, 'pages/reports.html')

@login_required
def commission_page(request):
    if request.user.role == 'agent':
        commissions = Commission.objects.filter(agent=request.user)
    else:
        commissions = Commission.objects.all()
    return render(request, 'pages/commission.html', {'commissions': commissions})

@login_required
def generate_report(request, report_type, format_type):
    if report_type == 'feeding':
        data = FeedingLog.objects.all()
        filename = f"feeding_report.{format_type}"
    elif report_type == 'plans':
        data = FeedPlan.objects.all()
        filename = f"feed_plans_report.{format_type}"
    else:
        return HttpResponse("Invalid report type", status=400)
    
    if format_type == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        p = canvas.Canvas(response)
        p.drawString(100, 750, f"{report_type.title()} Report")
        # Add more PDF content here
        p.save()
        
    elif format_type == 'xlsx':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        wb = Workbook()
        ws = wb.active
        ws.title = f"{report_type.title()} Report"
        # Add Excel content here
        wb.save(response)
        
    elif format_type == 'docx':
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        doc = Document()
        doc.add_heading(f'{report_type.title()} Report', 0)
        # Add Word content here
        doc.save(response)
    
    return response

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

# Get feed plan details for editing
@login_required
def get_feed_plan(request, plan_id):
    if request.method == 'GET':
        try:
            plan = FeedPlan.objects.get(id=plan_id, farmer=request.user)
            data = {
                'id': plan.id,
                'species_name': plan.species.name,
                'species_id': plan.species.id,
                'feed_type': plan.feed_type,
                'quantity_per_day': plan.quantity_per_day,
                'feeding_times': plan.feeding_times,
                'start_date': plan.start_date.strftime('%Y-%m-%d'),
                'end_date': plan.end_date.strftime('%Y-%m-%d'),
                'is_active': plan.is_active,
                'notes': plan.notes or ''
            }
            return JsonResponse(data)
        except FeedPlan.DoesNotExist:
            return JsonResponse({'error': 'Feed plan not found'}, status=404)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

# Edit feed plan
@login_required
@csrf_exempt
def edit_feed_plan(request, plan_id):
    if request.method == 'POST':
        try:
            plan = FeedPlan.objects.get(id=plan_id, farmer=request.user)
            data = json.loads(request.body)
            plan.feed_type = data.get('feed_type', plan.feed_type)
            plan.quantity_per_day = float(data.get('quantity_per_day', plan.quantity_per_day))
            plan.feeding_times = data.get('feeding_times', plan.feeding_times)
            plan.start_date = data.get('start_date', plan.start_date)
            plan.end_date = data.get('end_date', plan.end_date)
            plan.is_active = data.get('is_active', plan.is_active)
            plan.notes = data.get('notes', plan.notes)
            # Optionally allow species change
            species_id = data.get('species_id')
            if species_id:
                try:
                    plan.species = Species.objects.get(id=species_id)
                except Species.DoesNotExist:
                    pass
            plan.save()
            return JsonResponse({'success': True, 'message': 'Feed plan updated successfully'})
        except FeedPlan.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Feed plan not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
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