# Hospital Management System - API Quick Guide

## 🚀 Getting Started

### Base URL
```
http://localhost:5000
```

### Quick Health Check
```bash
curl http://localhost:5000/health
```

### API Information
```bash
curl http://localhost:5000/api/info
```

## 🔐 Authentication

### 1. Register a User
```bash
curl -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "fullname": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "phone_num": "+1234567890",
    "role": "user"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePass123!"
  }'
```

### 3. Admin Login
```bash
curl -X POST http://localhost:5000/auth/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@hospital.com",
    "password": "admin123"
  }'
```

### 4. Get Profile
```bash
curl -X GET http://localhost:5000/auth/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🏥 Hospital Management

### 1. Get All Hospitals
```bash
curl http://localhost:5000/hospital/all
```

### 2. Get Hospital Details
```bash
curl http://localhost:5000/hospital/1
```

### 3. Register Hospital (Admin Only)
```bash
curl -X POST http://localhost:5000/hospital/register \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -d '{
    "username": "cityhospital",
    "name": "City General Hospital",
    "type": "General",
    "email": "admin@cityhospital.com",
    "password": "HospitalPass123!",
    "location": "123 Main St, City",
    "contact_num": "+1234567890",
    "is_multi_level": true,
    "bedAvailability": 50,
    "oxygenUnits": 10
  }'
```

## 👨‍⚕️ Appointments

### 1. Book OPD Appointment
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

### 2. Get My Appointments
```bash
curl -X GET http://localhost:5000/appointment/my-appointments \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Get Available Slots
```bash
curl "http://localhost:5000/appointment/available-slots?hospital_id=1&date=2023-12-01"
```

## 🩸 Blood Bank

### 1. Get All Blood Banks
```bash
curl http://localhost:5000/bloodbank/all
```

### 2. Request Blood
```bash
curl -X POST http://localhost:5000/bloodbank/request \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "blood_type": "A+",
    "units_needed": 2,
    "urgency": "high",
    "hospital_id": 1,
    "reason": "Surgery required"
  }'
```

## 🚑 Emergency Services

### 1. Log Emergency
```bash
curl -X POST http://localhost:5000/emergency/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "emergency_type": "medical",
    "location": "123 Main St",
    "description": "Heart attack patient",
    "severity": "critical"
  }'
```

### 2. Get Available Ambulances
```bash
curl http://localhost:5000/emergency/ambulances/available
```

## 👥 User Management (Admin Only)

### 1. Get All Users
```bash
curl -X GET http://localhost:5000/user/all \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

### 2. Search Users
```bash
curl -X GET "http://localhost:5000/user/search?q=john" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

### 3. Update User Role
```bash
curl -X PUT http://localhost:5000/user/update-role/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \
  -d '{
    "role": "doctor"
  }'
```

## 📊 Analytics & Reporting (Admin Only)

### 1. Get Dashboard Stats
```bash
curl -X GET http://localhost:5000/admin/dashboard/stats \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

### 2. Get User Statistics
```bash
curl -X GET http://localhost:5000/user/stats \
  -H "Authorization: Bearer ADMIN_JWT_TOKEN"
```

## 🔍 Common Response Formats

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {
    // Response data here
  }
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

## 🔑 JWT Token Usage

After successful login, you'll receive an `access_token`. Use it in the Authorization header:

```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## 📝 Important Notes

1. **Content-Type**: Always use `application/json` for POST/PUT requests
2. **Authentication**: Most endpoints require JWT token in Authorization header
3. **Permissions**: Some endpoints require specific roles (admin, hospital_admin, etc.)
4. **Pagination**: List endpoints support pagination with `page` and `per_page` parameters
5. **Filtering**: Many GET endpoints support filtering parameters

## 🛠️ Testing with Postman

1. Import the API endpoints into Postman
2. Set up environment variables:
   - `base_url`: `http://localhost:5000`
   - `access_token`: Your JWT token after login
3. Use `{{base_url}}` and `{{access_token}}` in your requests

## 🐛 Error Handling

The API returns consistent HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `409`: Conflict
- `500`: Internal Server Error
