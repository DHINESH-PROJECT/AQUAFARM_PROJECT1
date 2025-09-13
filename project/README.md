# AquaCare - Fish Farming Management System

A comprehensive web application for managing fish farming operations with role-based access for Farmers, Producers, and Agents.

## Features

### For Farmers
- **Species Management**: Browse fish species with detailed care instructions
- **Feed Plans**: Create and manage feeding schedules
- **Feeding Logs**: Record daily feeding activities and fish health parameters
- **Order Tracking**: Monitor equipment and feed orders

### For Producers
- **Inventory Management**: Track fish, feed, and equipment stock levels
- **Order Management**: Process and fulfill farmer orders
- **Production Reports**: Monitor production metrics and quality
- **Species Database**: Maintain comprehensive species information

### For Agents
- **Delivery Tracking**: Monitor order delivery status
- **Communication Hub**: Coordinate between farmers and producers
- **Commission Tracking**: Monitor earnings and payment status
- **Route Optimization**: Manage delivery routes and workers

## Technology Stack

### Backend
- **Django 4.2** - Web framework
- **MySQL** - Database
- **Django REST Framework** - API development

### Frontend
- **HTML5, CSS3, JavaScript** - Core technologies
- **Bootstrap 5** - UI framework
- **Chart.js** - Data visualization
- **Font Awesome** - Icons

## Installation

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- pip (Python package manager)

### Backend Setup

1. **Create and activate virtual environment:**
```bash
python -m venv fish_farming_env
source fish_farming_env/bin/activate  # On Windows: fish_farming_env\Scripts\activate
```

2. **Install dependencies:**
```bash
cd backend
pip install -r requirements.txt
```

3. **Configure MySQL Database:**
   - Create a MySQL database named `fish_farming_db`
   - Update database credentials in `fish_farming/settings.py`

4. **Run migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

5. **Create superuser:**
```bash
python manage.py createsuperuser
```

6. **Load sample data:**
```bash
python manage.py create_sample_data
```

7. **Start development server:**
```bash
python manage.py runserver
```

### Frontend Setup

The frontend templates are located in `frontend/templates/` and static files in `frontend/static/`. 

Make sure to:
1. Copy the `templates` folder to your Django project's template directory
2. Copy the `static` folder to your Django project's static files directory
3. Configure `STATICFILES_DIRS` and `TEMPLATES` in Django settings

## Project Structure

```
backend/
├── fish_farming/          # Django project settings
├── fish_management/       # Main application
│   ├── models.py         # Database models
│   ├── views.py          # View functions
│   ├── urls.py           # URL routing
│   └── admin.py          # Admin interface
└── manage.py             # Django management script

frontend/
├── templates/
│   ├── base.html         # Base template
│   ├── home.html         # Landing page
│   ├── auth/             # Authentication pages
│   ├── dashboards/       # Role-specific dashboards
│   └── pages/            # Feature pages
└── static/
    ├── css/              # Stylesheets
    ├── js/               # JavaScript files
    └── images/           # Static images
```

## Database Models

- **User**: Extended Django user with role-based permissions
- **Species**: Fish species with care parameters
- **FeedPlan**: Feeding schedules linked to species and farmers
- **FeedingLog**: Daily feeding records with health metrics
- **Inventory**: Producer stock management
- **Order**: Order processing between farmers and producers
- **Delivery**: Delivery tracking with agent assignments
- **Commission**: Agent commission tracking

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/logout/` - User logout

### Core Features
- `GET /api/species/` - List all fish species
- `GET/POST /api/feed_plans/` - Manage feed plans
- `GET/POST /api/feeding_logs/` - Manage feeding logs
- `GET /api/inventory/` - View inventory items
- `GET /api/orders/` - Manage orders

### Reports
- `GET /generate_report/<type>/<format>/` - Generate reports (PDF, Excel, Word)

## Sample Data

The system includes 20+ sample records for each major entity:
- **Species**: 20+ fish species with complete care information
- **Feed Plans**: 25+ diverse feeding schedules
- **Feeding Logs**: 50+ daily feeding records
- **Inventory**: Comprehensive stock items
- **Orders**: 20+ sample orders across different statuses

## Security Features

- Role-based access control
- CSRF protection
- SQL injection prevention
- User authentication and authorization
- Secure password handling


## Responsive Design

The application is fully responsive with:
- Mobile-first approach
- Bootstrap grid system
- Optimized layouts for all devices
- Touch-friendly interfaces

## Browser Support

- Chrome (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers (iOS Safari, Chrome Mobile)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Email: support@aquacare.com
- Phone: +1 (555) 123-FISH
- Documentation: [Project Wiki]

## Acknowledgments

- Bootstrap team for the excellent UI framework
- Django community for the robust web framework
- Contributors and testers who helped improve the system