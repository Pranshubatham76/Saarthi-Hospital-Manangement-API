# Hospital Management System API Documentation Guide

## 🚀 API Documentation & Testing Interface

Your Hospital Management System now includes a comprehensive API documentation and testing interface that allows anyone to explore and test all available endpoints without needing Postman or other external tools.

## 📖 Available Documentation Interfaces

### 1. Interactive API Documentation (`/api-docs`)
- **URL**: `http://localhost:5000/api-docs`
- **Features**:
  - ✅ Beautiful, interactive interface with authentication support
  - ✅ Built-in API testing capabilities
  - ✅ Real-time request/response testing
  - ✅ Automatic JWT token management
  - ✅ Code examples for each endpoint
  - ✅ Quick actions for common operations

### 2. Swagger UI (`/swagger`)
- **URL**: `http://localhost:5000/swagger`
- **Features**:
  - ✅ Standard OpenAPI/Swagger interface
  - ✅ Complete API specification
  - ✅ Try-it-out functionality
  - ✅ Schema definitions
  - ✅ Authentication integration

### 3. API Information (`/api/info`)
- **URL**: `http://localhost:5000/api/info`
- **Features**:
  - ✅ Complete endpoint listing
  - ✅ Feature overview
  - ✅ Quick reference guide

### 4. API Testing Interface (`/api-test`)
- **URL**: `http://localhost:5000/api-test`
- **Features**:
  - ✅ JSON API for programmatic access
  - ✅ Endpoint discovery
  - ✅ Testing automation support

## 🏥 API Overview

Your Hospital Management System provides **89 endpoints** across **14 modules**:

### 🔐 Authentication & Authorization
- User registration and login
- Admin authentication
- Hospital account authentication
- JWT token management
- Profile management

### 🏥 Hospital Management
- Hospital registration
- Multi-level hospital support (floors, wards, beds)
- Hospital information management
- Bed availability tracking

### 👨‍⚕️ Doctor & Appointment Management  
- Doctor registration and profiles
- Schedule management
- OPD slot booking
- Appointment lifecycle management

### 🩸 Blood Bank System
- Blood bank registration
- Blood inventory management
- Blood request processing
- Stock tracking

### 🚑 Emergency Services
- Emergency call logging
- Ambulance dispatch
- Emergency case tracking
- Response management

### 👤 User Management
- User profiles and roles
- Role-based access control (RBAC)
- User statistics and reporting

### 📊 Admin Dashboard
- System statistics
- User management
- Audit logs
- System monitoring

### 🔔 Notifications
- Real-time notifications
- Email templates
- Broadcast messaging
- Notification preferences

### 📋 Audit & Compliance
- Comprehensive audit logging
- Security event tracking
- Compliance reporting
- Data access patterns

### 📈 Dashboard & Analytics
- Role-based dashboards
- System metrics
- Performance monitoring

## 🧪 How to Test Your API

### Method 1: Interactive Documentation (Recommended)

1. **Start your application**:
   ```bash
   python run.py
   ```

2. **Open the interactive documentation**:
   - Navigate to: `http://localhost:5000/api-docs`

3. **Authenticate**:
   - Use the authentication section at the top
   - Default admin credentials: `admin` / `admin123`
   - Click "Get Access Token"

4. **Test endpoints**:
   - Browse through the endpoint cards
   - Click "Test" tab on any endpoint
   - Modify request parameters/body as needed
   - Click the test button
   - View results in the "Response" tab

### Method 2: Swagger UI

1. **Navigate to Swagger UI**:
   - Go to: `http://localhost:5000/swagger`

2. **Authorize**:
   - Click the "Authorize" button
   - Enter: `Bearer {your-token}` (get token from `/auth/login`)

3. **Test endpoints**:
   - Expand any endpoint section
   - Click "Try it out"
   - Fill in parameters
   - Click "Execute"

### Method 3: Command Line Testing

```bash
# Health check
curl http://localhost:5000/health

# Register a new user
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "fullname": "Test User",
    "email": "test@example.com",
    "password": "SecurePass123!",
    "role": "user"
  }'

# Login and get token
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'

# Use token for protected endpoints
curl http://localhost:5000/auth/profile \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 🔑 Authentication Examples

### User Registration
```json
POST /auth/register
{
  "username": "john_doe",
  "fullname": "John Doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "phone_num": "+1234567890",
  "location": "New York, NY",
  "role": "user"
}
```

### Admin Login
```json
POST /auth/admin/login
{
  "username": "admin",
  "password": "admin123"
}
```

### Hospital Registration
```json
POST /hospital/register
{
  "username": "city_hospital",
  "name": "City General Hospital",
  "type": "General",
  "email": "admin@cityhospital.com",
  "password": "SecurePass123!",
  "location": "123 Main St, City, State",
  "reg_id": "REG123456",
  "is_multi_level": true
}
```

## 📊 Quick Actions Available

The interactive documentation includes these quick actions:

1. **Health Check**: Test API availability
2. **System Stats**: Get dashboard statistics (requires admin auth)
3. **List Hospitals**: View all registered hospitals
4. **My Profile**: View your user profile (requires auth)

## 🛡️ Security Features

- **JWT Authentication**: Secure token-based authentication
- **Role-Based Access Control (RBAC)**: Different permissions for users, hospitals, and admins
- **Audit Logging**: Comprehensive logging of all actions
- **Rate Limiting**: API protection against abuse
- **Input Validation**: Secure data handling

## 🔧 Development & Testing

### Route Discovery
A route discovery script is available to explore all endpoints:
```bash
python discover_routes.py
```

This will show:
- All available routes grouped by blueprint
- Authentication requirements
- HTTP methods supported
- Route summaries

### Database Initialization
The system automatically creates:
- Default admin user
- Ward categories (General, ICU, CCU, Maternity, etc.)
- Database tables

## 📝 API Response Format

All API responses follow this consistent format:

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error description",
  "error_code": 400
}
```

## 🚀 Production Deployment

When deploying to production:

1. **Update URLs**: Change `localhost:5000` to your production domain in documentation
2. **Environment Variables**: Set proper environment variables for production
3. **HTTPS**: Ensure all API calls use HTTPS in production
4. **Authentication**: Use strong passwords and proper JWT secrets

## 💡 Tips for API Testing

1. **Start with Authentication**: Always get your access token first
2. **Use Quick Actions**: Test basic functionality with the quick action buttons
3. **Check Response Tab**: Always review the response to understand the data structure
4. **Save Tokens**: The interface automatically saves your JWT token for protected endpoints
5. **Test Edge Cases**: Try invalid data to test error handling

## 🎯 Next Steps

1. Open `http://localhost:5000/api-docs` and start exploring
2. Test authentication with the default admin credentials
3. Try creating a hospital and user accounts
4. Test the appointment booking flow
5. Explore the emergency and blood bank features

## 📞 Support

If you encounter any issues:
1. Check the application logs
2. Verify your authentication token
3. Ensure the database is properly initialized
4. Test with the health check endpoint first

---

**Congratulations!** 🎉 Your Hospital Management System now has a comprehensive, professional API documentation and testing interface that rivals any commercial API platform.