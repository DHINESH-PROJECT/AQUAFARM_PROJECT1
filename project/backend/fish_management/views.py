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
def reports_page(request):
    return render(request, 'pages/reports.html')

@login_required
def commission_page(request):
    if request.user.role == 'agent':
        commissions = Commission.objects.filter(agent=request.user)
    else:
        commissions = Commission.objects.all()
    return render(request, 'pages/commission.html', {'commissions': commissions})

def generate_report(request, report_type, format_type):
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    species_filter = request.GET.get('species')
    
    # Base filename
    timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
    
    if report_type == 'feeding':
        return generate_feeding_report(request, format_type, start_date, end_date, species_filter, timestamp)
    elif report_type == 'plans':
        return generate_feed_plans_report(request, format_type, start_date, end_date, species_filter, timestamp)
    elif report_type == 'inventory':
        return generate_inventory_report(request, format_type, timestamp)
    elif report_type == 'orders':
        return generate_orders_report(request, format_type, start_date, end_date, timestamp)
    elif report_type == 'commission':
        return generate_commission_report(request, format_type, start_date, end_date, timestamp)
    else:
        return HttpResponse("Invalid report type", status=400)

def generate_feeding_report(request, format_type, start_date, end_date, species_filter, timestamp):
    # Filter data based on user role and parameters
    queryset = FeedingLog.objects.all()
    
    if request.user.role == 'farmer':
        queryset = queryset.filter(farmer=request.user)
    
    if start_date:
        queryset = queryset.filter(feeding_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(feeding_date__lte=end_date)
    if species_filter:
        queryset = queryset.filter(feed_plan__species__name=species_filter)
    
    data = queryset.select_related('feed_plan__species', 'farmer').order_by('-feeding_date')
    filename = f"feeding_report_{timestamp}.{format_type}"
    
    if format_type == 'pdf':
        return generate_feeding_pdf(data, filename, request.user)
    elif format_type == 'xlsx':
        return generate_feeding_excel(data, filename, request.user)
    else:
        return HttpResponse("Invalid format type", status=400)

def generate_feeding_pdf(data, filename, user):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor=colors.HexColor('#1e3a8a')
    )
    story.append(Paragraph("AquaCare - Feeding Activity Report", title_style))
    story.append(Spacer(1, 20))
    
    # Report info
    info_style = styles['Normal']
    story.append(Paragraph(f"Generated for: {user.username} ({user.role.title()})", info_style))
    story.append(Paragraph(f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", info_style))
    story.append(Paragraph(f"Total Records: {data.count()}", info_style))
    story.append(Spacer(1, 20))
    
    if data.exists():
        # Create table data
        table_data = [
            ['Date', 'Time', 'Species', 'Farmer', 'Quantity (kg)', 'Water Temp (°C)', 'pH Level', 'Mortality', 'Notes']
        ]
        
        for log in data:
            table_data.append([
                log.feeding_date.strftime('%Y-%m-%d'),
                log.feeding_time.strftime('%H:%M'),
                log.feed_plan.species.name,
                log.farmer.username,
                str(log.quantity_fed),
                str(log.water_temperature) if log.water_temperature else 'N/A',
                str(log.ph_level) if log.ph_level else 'N/A',
                str(log.mortality_count),
                log.notes[:30] + '...' if log.notes and len(log.notes) > 30 else log.notes or 'N/A'
            ])
        
        # Create table
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        
        # Summary statistics
        story.append(Spacer(1, 30))
        story.append(Paragraph("Summary Statistics", styles['Heading2']))
        
        total_quantity = sum(log.quantity_fed for log in data)
        avg_temp = data.filter(water_temperature__isnull=False).aggregate(Avg('water_temperature'))['water_temperature__avg']
        avg_ph = data.filter(ph_level__isnull=False).aggregate(Avg('ph_level'))['ph_level__avg']
        total_mortality = sum(log.mortality_count for log in data)
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Feed Quantity', f"{total_quantity:.2f} kg"],
            ['Average Water Temperature', f"{avg_temp:.2f}°C" if avg_temp else 'N/A'],
            ['Average pH Level', f"{avg_ph:.2f}" if avg_ph else 'N/A'],
            ['Total Mortality Count', str(total_mortality)]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9488')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
    else:
        story.append(Paragraph("No feeding records found for the selected criteria.", styles['Normal']))
    
    doc.build(story)
    return response

def generate_feeding_excel(data, filename, user):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Feeding Report"
    
    # Header styling
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Title
    ws.merge_cells('A1:I1')
    ws['A1'] = "AquaCare - Feeding Activity Report"
    ws['A1'].font = Font(bold=True, size=16, color="1E3A8A")
    ws['A1'].alignment = Alignment(horizontal="center")
    
    # Report info
    ws['A3'] = f"Generated for: {user.username} ({user.role.title()})"
    ws['A4'] = f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}"
    ws['A5'] = f"Total Records: {data.count()}"
    
    # Headers
    headers = ['Date', 'Time', 'Species', 'Farmer', 'Quantity (kg)', 'Water Temp (°C)', 'pH Level', 'Mortality', 'Notes']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=7, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    # Data rows
    for row, log in enumerate(data, 8):
        ws.cell(row=row, column=1, value=log.feeding_date.strftime('%Y-%m-%d'))
        ws.cell(row=row, column=2, value=log.feeding_time.strftime('%H:%M'))
        ws.cell(row=row, column=3, value=log.feed_plan.species.name)
        ws.cell(row=row, column=4, value=log.farmer.username)
        ws.cell(row=row, column=5, value=log.quantity_fed)
        ws.cell(row=row, column=6, value=log.water_temperature if log.water_temperature else 'N/A')
        ws.cell(row=row, column=7, value=log.ph_level if log.ph_level else 'N/A')
        ws.cell(row=row, column=8, value=log.mortality_count)
        ws.cell(row=row, column=9, value=log.notes or 'N/A')
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    wb.save(response)
    return response

def generate_feed_plans_report(request, format_type, start_date, end_date, species_filter, timestamp):
    queryset = FeedPlan.objects.all()
    
    if request.user.role == 'farmer':
        queryset = queryset.filter(farmer=request.user)
    
    if start_date:
        queryset = queryset.filter(start_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(end_date__lte=end_date)
    if species_filter:
        queryset = queryset.filter(species__name=species_filter)
    
    data = queryset.select_related('species', 'farmer').order_by('-created_at')
    filename = f"feed_plans_report_{timestamp}.{format_type}"
    
    if format_type == 'pdf':
        return generate_feed_plans_pdf(data, filename, request.user)
    elif format_type == 'xlsx':
        return generate_feed_plans_excel(data, filename, request.user)

def generate_feed_plans_pdf(data, filename, user):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,
        textColor=colors.HexColor('#1e3a8a')
    )
    story.append(Paragraph("AquaCare - Feed Plans Report", title_style))
    story.append(Spacer(1, 20))
    
    # Report info
    info_style = styles['Normal']
    story.append(Paragraph(f"Generated for: {user.username} ({user.role.title()})", info_style))
    story.append(Paragraph(f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", info_style))
    story.append(Paragraph(f"Total Plans: {data.count()}", info_style))
    story.append(Spacer(1, 20))
    
    if data.exists():
        table_data = [
            ['Species', 'Farmer', 'Feed Type', 'Quantity/Day (kg)', 'Start Date', 'End Date', 'Status', 'Feeding Times']
        ]
        
        for plan in data:
            feeding_times = ', '.join(plan.feeding_times) if plan.feeding_times else 'N/A'
            table_data.append([
                plan.species.name,
                plan.farmer.username,
                plan.feed_type,
                str(plan.quantity_per_day),
                plan.start_date.strftime('%Y-%m-%d'),
                plan.end_date.strftime('%Y-%m-%d'),
                'Active' if plan.is_active else 'Inactive',
                feeding_times[:20] + '...' if len(feeding_times) > 20 else feeding_times
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No feed plans found for the selected criteria.", styles['Normal']))
    
    doc.build(story)
    return response

def generate_feed_plans_excel(data, filename, user):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Feed Plans Report"
    
    # Header styling
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    # Title
    ws.merge_cells('A1:H1')
    ws['A1'] = "AquaCare - Feed Plans Report"
    ws['A1'].font = Font(bold=True, size=16, color="1E3A8A")
    ws['A1'].alignment = Alignment(horizontal="center")
    
    # Report info
    ws['A3'] = f"Generated for: {user.username} ({user.role.title()})"
    ws['A4'] = f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}"
    ws['A5'] = f"Total Plans: {data.count()}"
    
    # Headers
    headers = ['Species', 'Farmer', 'Feed Type', 'Quantity/Day (kg)', 'Start Date', 'End Date', 'Status', 'Feeding Times']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=7, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    # Data rows
    for row, plan in enumerate(data, 8):
        ws.cell(row=row, column=1, value=plan.species.name)
        ws.cell(row=row, column=2, value=plan.farmer.username)
        ws.cell(row=row, column=3, value=plan.feed_type)
        ws.cell(row=row, column=4, value=plan.quantity_per_day)
        ws.cell(row=row, column=5, value=plan.start_date.strftime('%Y-%m-%d'))
        ws.cell(row=row, column=6, value=plan.end_date.strftime('%Y-%m-%d'))
        ws.cell(row=row, column=7, value='Active' if plan.is_active else 'Inactive')
        ws.cell(row=row, column=8, value=', '.join(plan.feeding_times) if plan.feeding_times else 'N/A')
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    wb.save(response)
    return response

def generate_inventory_report(request, format_type, timestamp):
    queryset = Inventory.objects.all()
    
    if request.user.role == 'producer':
        queryset = queryset.filter(producer=request.user)
    
    data = queryset.select_related('producer').order_by('item_type', 'item_name')
    filename = f"inventory_report_{timestamp}.{format_type}"
    
    if format_type == 'pdf':
        return generate_inventory_pdf(data, filename, request.user)
    elif format_type == 'xlsx':
        return generate_inventory_excel(data, filename, request.user)

def generate_inventory_pdf(data, filename, user):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,
        textColor=colors.HexColor('#1e3a8a')
    )
    story.append(Paragraph("AquaCare - Inventory Report", title_style))
    story.append(Spacer(1, 20))
    
    info_style = styles['Normal']
    story.append(Paragraph(f"Generated for: {user.username} ({user.role.title()})", info_style))
    story.append(Paragraph(f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", info_style))
    story.append(Paragraph(f"Total Items: {data.count()}", info_style))
    story.append(Spacer(1, 20))
    
    if data.exists():
        table_data = [
            ['Item Name', 'Category', 'Quantity', 'Unit', 'Price/Unit', 'Total Value', 'Min Stock', 'Status']
        ]
        
        for item in data:
            total_value = float(item.quantity) * float(item.price_per_unit)
            status = 'Low Stock' if item.quantity <= item.minimum_stock else 'In Stock'
            table_data.append([
                item.item_name,
                item.item_type.title(),
                str(item.quantity),
                item.unit,
                f"${item.price_per_unit}",
                f"${total_value:.2f}",
                str(item.minimum_stock),
                status
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    else:
        story.append(Paragraph("No inventory items found.", styles['Normal']))
    
    doc.build(story)
    return response

def generate_inventory_excel(data, filename, user):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventory Report"
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    ws.merge_cells('A1:H1')
    ws['A1'] = "AquaCare - Inventory Report"
    ws['A1'].font = Font(bold=True, size=16, color="1E3A8A")
    ws['A1'].alignment = Alignment(horizontal="center")
    
    ws['A3'] = f"Generated for: {user.username} ({user.role.title()})"
    ws['A4'] = f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}"
    ws['A5'] = f"Total Items: {data.count()}"
    
    headers = ['Item Name', 'Category', 'Quantity', 'Unit', 'Price/Unit', 'Total Value', 'Min Stock', 'Status']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=7, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    for row, item in enumerate(data, 8):
        total_value = float(item.quantity) * float(item.price_per_unit)
        status = 'Low Stock' if item.quantity <= item.minimum_stock else 'In Stock'
        
        ws.cell(row=row, column=1, value=item.item_name)
        ws.cell(row=row, column=2, value=item.item_type.title())
        ws.cell(row=row, column=3, value=item.quantity)
        ws.cell(row=row, column=4, value=item.unit)
        ws.cell(row=row, column=5, value=float(item.price_per_unit))
        ws.cell(row=row, column=6, value=total_value)
        ws.cell(row=row, column=7, value=item.minimum_stock)
        ws.cell(row=row, column=8, value=status)
    
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    wb.save(response)
    return response

def generate_orders_report(request, format_type, start_date, end_date, timestamp):
    queryset = Order.objects.all()
    
    if request.user.role == 'farmer':
        queryset = queryset.filter(customer=request.user)
    elif request.user.role == 'producer':
        queryset = queryset.filter(producer=request.user)
    
    if start_date:
        queryset = queryset.filter(order_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(order_date__lte=end_date)
    
    data = queryset.select_related('customer', 'producer', 'inventory_item').order_by('-order_date')
    filename = f"orders_report_{timestamp}.{format_type}"
    
    if format_type == 'pdf':
        return generate_orders_pdf(data, filename, request.user)
    elif format_type == 'xlsx':
        return generate_orders_excel(data, filename, request.user)

def generate_orders_pdf(data, filename, user):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,
        textColor=colors.HexColor('#1e3a8a')
    )
    story.append(Paragraph("AquaCare - Orders Report", title_style))
    story.append(Spacer(1, 20))
    
    info_style = styles['Normal']
    story.append(Paragraph(f"Generated for: {user.username} ({user.role.title()})", info_style))
    story.append(Paragraph(f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", info_style))
    story.append(Paragraph(f"Total Orders: {data.count()}", info_style))
    story.append(Spacer(1, 20))
    
    if data.exists():
        table_data = [
            ['Order ID', 'Customer', 'Producer', 'Item', 'Quantity', 'Total Price', 'Status', 'Order Date']
        ]
        
        for order in data:
            table_data.append([
                f"#ORD-{order.id:03d}",
                order.customer.username,
                order.producer.username,
                order.inventory_item.item_name,
                f"{order.quantity} {order.inventory_item.unit}",
                f"${order.total_price}",
                order.status.title(),
                order.order_date.strftime('%Y-%m-%d')
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        
        # Summary
        story.append(Spacer(1, 30))
        story.append(Paragraph("Order Summary", styles['Heading2']))
        
        total_value = sum(float(order.total_price) for order in data)
        status_counts = {}
        for order in data:
            status_counts[order.status] = status_counts.get(order.status, 0) + 1
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Order Value', f"${total_value:.2f}"],
            ['Average Order Value', f"${total_value/data.count():.2f}" if data.count() > 0 else "$0.00"]
        ]
        
        for status, count in status_counts.items():
            summary_data.append([f"{status.title()} Orders", str(count)])
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9488')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
    else:
        story.append(Paragraph("No orders found for the selected criteria.", styles['Normal']))
    
    doc.build(story)
    return response

def generate_orders_excel(data, filename, user):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Orders Report"
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")
    
    ws.merge_cells('A1:H1')
    ws['A1'] = "AquaCare - Orders Report"
    ws['A1'].font = Font(bold=True, size=16, color="1E3A8A")
    ws['A1'].alignment = Alignment(horizontal="center")
    
    ws['A3'] = f"Generated for: {user.username} ({user.role.title()})"
    ws['A4'] = f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}"
    ws['A5'] = f"Total Orders: {data.count()}"
    
    headers = ['Order ID', 'Customer', 'Producer', 'Item', 'Quantity', 'Total Price', 'Status', 'Order Date']
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=7, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
    
    for row, order in enumerate(data, 8):
        ws.cell(row=row, column=1, value=f"#ORD-{order.id:03d}")
        ws.cell(row=row, column=2, value=order.customer.username)
        ws.cell(row=row, column=3, value=order.producer.username)
        ws.cell(row=row, column=4, value=order.inventory_item.item_name)
        ws.cell(row=row, column=5, value=f"{order.quantity} {order.inventory_item.unit}")
        ws.cell(row=row, column=6, value=float(order.total_price))
        ws.cell(row=row, column=7, value=order.status.title())
        ws.cell(row=row, column=8, value=order.order_date.strftime('%Y-%m-%d'))
    
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    wb.save(response)
    return response

def generate_commission_report(request, format_type, start_date, end_date, timestamp):
    queryset = Commission.objects.all()
    
    if request.user.role == 'agent':
        queryset = queryset.filter(agent=request.user)
    
    if start_date:
        queryset = queryset.filter(created_at__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__lte=end_date)
    
    data = queryset.select_related('agent', 'order__customer', 'order__inventory_item').order_by('-created_at')
    filename = f"commission_report_{timestamp}.{format_type}"
    
    if format_type == 'pdf':
        return generate_commission_pdf(data, filename, request.user)
    elif format_type == 'xlsx':
        return generate_commission_excel(data, filename, request.user)

def generate_commission_pdf(data, filename, user):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,
        textColor=colors.HexColor('#1e3a8a')
    )
    story.append(Paragraph("AquaCare - Commission Report", title_style))
    story.append(Spacer(1, 20))
    
    info_style = styles['Normal']
    story.append(Paragraph(f"Generated for: {user.username} ({user.role.title()})", info_style))
    story.append(Paragraph(f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}", info_style))
    story.append(Paragraph(f"Total Records: {data.count()}", info_style))
    story.append(Spacer(1, 20))
    
    if data.exists():
        table_data = [
            ['Order ID', 'Agent', 'Customer', 'Order Value', 'Commission Rate', 'Commission Amount', 'Status', 'Date']
        ]
        
        for commission in data:
            table_data.append([
                f"#ORD-{commission.order.id:03d}",
                commission.agent.username,
                commission.order.customer.username,
                f"${commission.order.total_price}",
                f"{commission.commission_rate}%",
                f"${commission.commission_amount}",
                'Paid' if commission.is_paid else 'Pending',
                commission.created_at.strftime('%Y-%m-%d')
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        
        # Summary
        story.append(Spacer(1, 30))
        story.append(Paragraph("Commission Summary", styles['Heading2']))
        
        total_commission = sum(float(c.commission_amount) for c in data)
        paid_commission = sum(float(c.commission_amount) for c in data if c.is_paid)
        pending_commission = total_commission - paid_commission
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Commission Earned', f"${total_commission:.2f}"],
            ['Paid Commission', f"${paid_commission:.2f}"],
            ['Pending Commission', f"${pending_commission:.2f}"],
            ['Average Commission per Order', f"${total_commission/data.count():.2f}" if data.count() > 0 else "$0.00"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0d9488')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
    else:
        story.append(Paragraph("No commission records found for the selected criteria.", styles['Normal']))
    
    doc.build(story)
    return response

def generate_commission_excel(data, filename, user):
    if hasattr(user, 'role') and hasattr(user, 'username'):
        # Default: generate xlsx
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        wb = Workbook()
        ws = wb.active
        ws.title = "Commission Report"
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        header_alignment = Alignment(horizontal="center", vertical="center")
        ws.merge_cells('A1:H1')
        ws['A1'] = "AquaCare - Commission Report"
        ws['A1'].font = Font(bold=True, size=16, color="1E3A8A")
        ws['A1'].alignment = Alignment(horizontal="center")
        ws['A3'] = f"Generated for: {user.username} ({user.role.title()})"
        ws['A4'] = f"Generated on: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}"
        ws['A5'] = f"Total Records: {data.count()}"
        headers = ['Order ID', 'Agent', 'Customer', 'Order Value', 'Commission Rate', 'Commission Amount', 'Status', 'Date']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=7, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        for row, commission in enumerate(data, 8):
            ws.cell(row=row, column=1, value=f"#ORD-{commission.order.id:03d}")
            ws.cell(row=row, column=2, value=commission.agent.username)
            ws.cell(row=row, column=3, value=commission.order.customer.username)
            ws.cell(row=row, column=4, value=float(commission.order.total_price))
            ws.cell(row=row, column=5, value=float(commission.commission_rate))
            ws.cell(row=row, column=6, value=float(commission.commission_amount))
            ws.cell(row=row, column=7, value='Paid' if commission.is_paid else 'Pending')
            ws.cell(row=row, column=8, value=commission.created_at.strftime('%Y-%m-%d'))
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
        wb.save(response)
        return response
    else:
        # fallback or error
        return HttpResponse('Invalid user or format', status=400)

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