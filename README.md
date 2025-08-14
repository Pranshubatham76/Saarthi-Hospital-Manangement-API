# Hospital Management System API

A comprehensive RESTful API for hospital management system built with Flask, featuring JWT authentication, role-based access control (RBAC), and complete healthcare management capabilities. This is a pure backend API designed to be consumed by frontend applications or mobile apps.

## Features

### 🔐 Authentication & Authorization
- JWT-based authentication with access and refresh tokens
- Role-based access control (RBAC)
- Multiple user types: patients, doctors, hospital admins, system admins
- Secure password hashing with bcrypt

### 🏥 Hospital Management
- Multi-level hospital support (floors, wards, beds)
- Single-level hospital configuration
- Real-time bed availability tracking
- Hospital registration and management
- OPD status management

### 👨‍⚕️ Doctor & Appointment Management
- Doctor registration and scheduling
- OPD slot management with capacity control
- Appointment booking and cancellation
- Real-time slot availability
- Visit and prescription tracking

### 🩸 Blood Bank System
- Blood inventory management
- Stock level tracking with expiry dates
- Blood request processing
- Multi-blood bank support
- Real-time stock updates

### 🚑 Emergency Services
- Emergency logging and tracking
- Ambulance management
- Status updates and forwarding
- Real-time location tracking support

### 📊 Dashboard & Analytics
- Role-based dashboards
- Real-time statistics
- User activity tracking
- System health monitoring

## Technology Stack

- **Backend**: Flask, Python 3.8+
- **Database**: SQLAlchemy (supports PostgreSQL, MySQL, SQLite)
- **Authentication**: JWT tokens with Flask-JWT-Extended
- **Security**: bcrypt password hashing, CORS enabled
- **API**: RESTful API design
- **Database Migrations**: Flask-Migrate

## Quick Start

### Prerequisites
- Python 3.8 or higher
- PostgreSQL (recommended) or SQLite for development

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hospital_management_system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Copy and edit the .env file
   cp .env.example .env
   
   # Edit .env with your database and configuration details
   ```

5. **Initialize database**
   ```bash
   python run.py
   ```

6. **Start the application**
   ```bash
   python run.py
   ```

The application will be available at `http://localhost:5000`

## Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Flask Configuration
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_SECRET_KEY=jwt-secret-string-change-this-too

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost/hospital_management
# For SQLite development: DATABASE_URL=sqlite:///hospital_management.db

# Admin Configuration
ADMIN_EMAIL=admin@hospital.com
ADMIN_PASSWORD=admin123

# JWT Configuration
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour
JWT_REFRESH_TOKEN_EXPIRES=2592000  # 30 days
```

### Database Setup

#### PostgreSQL (Recommended for Production)
```sql
CREATE DATABASE hospital_management;
CREATE USER hospital_user WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE hospital_management TO hospital_user;
```

#### SQLite (Development)
SQLite database will be created automatically in development mode.

## API Documentation

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | User login | No |
| POST | `/auth/admin/login` | Admin login | No |
| POST | `/auth/hospital/login` | Hospital admin login | No |
| POST | `/auth/refresh` | Refresh access token | Refresh Token |
| POST | `/auth/logout` | User logout | JWT |
| GET | `/auth/profile` | Get user profile | JWT |
| POST | `/auth/change-password` | Change password | JWT |

### Hospital Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/hospital/register` | Register hospital | Admin |
| GET | `/hospital/all` | Get all hospitals | Public |
| GET | `/hospital/<id>` | Get hospital details | Public |
| PUT | `/hospital/update/<id>` | Update hospital | Admin/Hospital Admin |
| DELETE | `/hospital/delete/<id>` | Delete hospital | Admin |
| POST | `/hospital/<id>/floors/create` | Create floor | Admin/Hospital Admin |
| GET | `/hospital/<id>/floors` | Get hospital floors | Public |

### Appointment System

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/appointment/opd/book` | Book OPD appointment | JWT |
| GET | `/appointment/opd/<id>` | Get appointment details | JWT |
| PUT | `/appointment/opd/update/<id>` | Update appointment | JWT |
| DELETE | `/appointment/opd/cancel/<id>` | Cancel appointment | JWT |
| GET | `/appointment/my-appointments` | Get user appointments | JWT |
| GET | `/appointment/available-slots` | Get available slots | Public |

### Blood Bank Management

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/bloodbank/register` | Register blood bank | Admin |
| GET | `/bloodbank/all` | Get all blood banks | Public |
| POST | `/bloodbank/<id>/addstock` | Add blood stock | Admin |
| GET | `/bloodbank/<id>/stock` | Get blood stock | Public |
| POST | `/bloodbank/request` | Request blood | JWT |
| GET | `/bloodbank/requests` | Get blood requests | JWT |

## User Roles and Permissions

### System Administrator (`admin`)
- Full system access
- User management
- Hospital registration and management
- System configuration
- Access to all data and logs

### Hospital Administrator (`hospital_admin`)
- Manage their own hospital
- Floor, ward, and bed management
- View hospital appointments
- Manage hospital staff
- Update hospital information

### Doctor (`doctor`)
- View and manage their appointments
- Access patient information for their appointments
- Update appointment status
- Manage their schedule

### Regular User (`user`)
- Book appointments
- View their own appointments
- Update their profile
- Request blood
- Log emergency requests

### Donor (`donor`)
- Same as regular user
- Additional donor-specific features

### Ambulance Driver (`ambulance_driver`)
- Update ambulance location and status
- View assigned emergency requests

## Database Schema

The system includes the following main entities:

- **Users**: System users with different roles
- **Admin**: System administrators
- **Hospital_info**: Hospital authentication information
- **Hospital**: Hospital operational data
- **Floor**: Hospital floors (for multi-level hospitals)
- **Ward**: Hospital wards within floors
- **Bed**: Individual beds with status tracking
- **Doctors_Info**: Doctor information and specializations
- **Appointment**: Appointment bookings
- **OPD**: Outpatient department configurations
- **opdSlots**: Available appointment slots
- **BloodBank**: Blood bank information
- **BloodInventory**: Blood stock management
- **Emergency**: Emergency requests
- **Ambulance**: Ambulance fleet management

## Development

### Running Tests
```bash
pytest tests/
```

### Database Migrations
```bash
# Initialize migrations (first time only)
flask db init

# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
```

### Code Style
The project follows PEP 8 style guidelines. Use `black` and `flake8` for code formatting:

```bash
pip install black flake8
black .
flake8 .
```

## Deployment

### Using Gunicorn (Production)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Using Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]
```

### Environment Setup for Production
1. Set `FLASK_ENV=production`
2. Use strong SECRET_KEY and JWT_SECRET_KEY
3. Configure PostgreSQL database
4. Set up SSL/TLS certificates
5. Configure reverse proxy (nginx)

## API Usage Examples

### User Registration
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "fullname": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "phone_num": "+1234567890",
    "role": "user"
  }'
```

### User Login
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123!"
  }'
```

### Book OPD Appointment
```bash
curl -X POST http://localhost:5000/appointment/opd/book \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "hospital_id": 1,
    "slot_id": 1,
    "reason": "Regular checkup"
  }'
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions, please contact:
- Email: support@hospitalmanagementsystem.com
- Issues: [GitHub Issues](https://github.com/yourusername/hospital_management_system/issues)

## Changelog

### v1.0.0 (Current)
- Initial release
- Complete authentication system with JWT and RBAC
- Hospital management with multi-level support
- Appointment booking system
- Blood bank management
- Emergency services
- Admin dashboard
- RESTful API with comprehensive endpoints
