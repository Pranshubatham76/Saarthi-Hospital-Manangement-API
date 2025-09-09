from flask import Blueprint, jsonify, render_template_string
from flasgger import Swagger, swag_from

swagger_bp = Blueprint('swagger', __name__)

# Define swagger template
swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Hospital Management System API",
        "description": "Comprehensive API for Hospital Management System with JWT Authentication and RBAC",
        "version": "1.0.0",
        "contact": {
            "name": "Hospital Management System",
            "email": "admin@hospital.com"
        }
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": [
        "http",
        "https"
    ],
    "securityDefinitions": {
        "JWT": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Enter: Bearer {your-token}"
        }
    },
    "consumes": [
        "application/json"
    ],
    "produces": [
        "application/json"
    ],
    "tags": [
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints"
        },
        {
            "name": "Users",
            "description": "User management endpoints"
        },
        {
            "name": "Hospitals",
            "description": "Hospital management endpoints"
        },
        {
            "name": "Doctors",
            "description": "Doctor management endpoints"
        },
        {
            "name": "Appointments",
            "description": "Appointment booking and management endpoints"
        },
        {
            "name": "Blood Bank",
            "description": "Blood bank management endpoints"
        },
        {
            "name": "Emergency",
            "description": "Emergency services endpoints"
        },
        {
            "name": "Admin",
            "description": "Administrative endpoints"
        },
        {
            "name": "Dashboard",
            "description": "Dashboard and statistics endpoints"
        },
        {
            "name": "Audit",
            "description": "Audit logging endpoints"
        },
        {
            "name": "Notifications",
            "description": "Notification management endpoints"
        }
    ]
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/swagger/"
}

def init_swagger(app):
    """Initialize Swagger for the Flask app"""
    swagger = Swagger(app, config=swagger_config, template=swagger_template)
    return swagger

@swagger_bp.route('/swagger')
def swagger_ui():
    """Swagger UI endpoint"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hospital Management System API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui.css" />
        <style>
            html {
                box-sizing: border-box;
                overflow: -moz-scrollbars-vertical;
                overflow-y: scroll;
            }
            *, *:before, *:after {
                box-sizing: inherit;
            }
            body {
                margin:0;
                background: #fafafa;
            }
            .swagger-ui .topbar { background-color: #2b7ec1; }
            .swagger-ui .topbar .download-url-wrapper .select-label { color: white; }
            .swagger-ui .topbar .download-url-wrapper input[type=text] { 
                min-width: 350px; 
                margin: 0;
            }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui-standalone-preset.js"></script>
        <script>
        window.onload = function() {
            const ui = SwaggerUIBundle({
                url: '/swagger.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                requestInterceptor: function(req) {
                    // Add authorization header from localStorage if available
                    const token = localStorage.getItem('access_token');
                    if (token) {
                        req.headers.Authorization = 'Bearer ' + token;
                    }
                    return req;
                }
            });
        }
        </script>
    </body>
    </html>
    """)

@swagger_bp.route('/swagger.json')
def swagger_json():
    """Generate complete Swagger JSON specification"""
    return jsonify({
        "swagger": "2.0",
        "info": {
            "title": "Hospital Management System API",
            "description": "Comprehensive API for Hospital Management System with JWT Authentication and RBAC",
            "version": "1.0.0",
            "contact": {
                "name": "Hospital Management System",
                "email": "admin@hospital.com"
            }
        },
        "host": "localhost:5000",
        "basePath": "/",
        "schemes": ["http", "https"],
        "securityDefinitions": {
            "JWT": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Enter: Bearer {your-token}"
            }
        },
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "tags": [
            {"name": "Authentication", "description": "User authentication and authorization endpoints"},
            {"name": "Users", "description": "User management endpoints"},
            {"name": "Hospitals", "description": "Hospital management endpoints"},
            {"name": "Doctors", "description": "Doctor management endpoints"},
            {"name": "Appointments", "description": "Appointment booking and management endpoints"},
            {"name": "Blood Bank", "description": "Blood bank management endpoints"},
            {"name": "Emergency", "description": "Emergency services endpoints"},
            {"name": "Admin", "description": "Administrative endpoints"},
            {"name": "Dashboard", "description": "Dashboard and statistics endpoints"},
            {"name": "Audit", "description": "Audit logging endpoints"},
            {"name": "Notifications", "description": "Notification management endpoints"}
        ],
        "paths": get_api_paths()
    })

def get_api_paths():
    """Generate all API paths with their specifications"""
    return {
        # Authentication endpoints
        "/auth/register": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Register a new user",
                "description": "Create a new user account with email verification",
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["username", "fullname", "email", "password"],
                            "properties": {
                                "username": {"type": "string", "example": "john_doe"},
                                "fullname": {"type": "string", "example": "John Doe"},
                                "email": {"type": "string", "format": "email", "example": "john@example.com"},
                                "password": {"type": "string", "minLength": 8, "example": "SecurePass123!"},
                                "phone_num": {"type": "string", "example": "+1234567890"},
                                "location": {"type": "string", "example": "New York, NY"},
                                "role": {"type": "string", "enum": ["user", "donor", "ambulance_driver"], "example": "user"}
                            }
                        }
                    }
                ],
                "responses": {
                    "201": {
                        "description": "User registered successfully",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "success": {"type": "boolean", "example": True},
                                "message": {"type": "string", "example": "User registered successfully"},
                                "data": {
                                    "type": "object",
                                    "properties": {
                                        "user_id": {"type": "integer", "example": 1},
                                        "username": {"type": "string", "example": "john_doe"},
                                        "email": {"type": "string", "example": "john@example.com"},
                                        "role": {"type": "string", "example": "user"}
                                    }
                                }
                            }
                        }
                    },
                    "400": {"description": "Invalid input data"},
                    "409": {"description": "User already exists"}
                }
            }
        },
        "/auth/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "User login",
                "description": "Authenticate user and return JWT tokens",
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["email", "password"],
                            "properties": {
                                "email": {"type": "string", "format": "email", "example": "john@example.com"},
                                "password": {"type": "string", "example": "SecurePass123!"}
                            }
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Login successful",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "success": {"type": "boolean", "example": True},
                                "message": {"type": "string", "example": "Login successful"},
                                "data": {
                                    "type": "object",
                                    "properties": {
                                        "access_token": {"type": "string", "example": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."},
                                        "refresh_token": {"type": "string", "example": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."},
                                        "user": {
                                            "type": "object",
                                            "properties": {
                                                "id": {"type": "integer", "example": 1},
                                                "username": {"type": "string", "example": "john_doe"},
                                                "email": {"type": "string", "example": "john@example.com"},
                                                "role": {"type": "string", "example": "user"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "Invalid credentials"},
                    "400": {"description": "Invalid input data"}
                }
            }
        },
        "/auth/admin/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Admin login",
                "description": "Authenticate admin user and return JWT tokens",
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["username", "password"],
                            "properties": {
                                "username": {"type": "string", "example": "admin"},
                                "password": {"type": "string", "example": "admin123"}
                            }
                        }
                    }
                ],
                "responses": {
                    "200": {"description": "Admin login successful"},
                    "401": {"description": "Invalid admin credentials"}
                }
            }
        },
        "/auth/hospital/login": {
            "post": {
                "tags": ["Authentication"],
                "summary": "Hospital login",
                "description": "Authenticate hospital account and return JWT tokens",
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["username", "password"],
                            "properties": {
                                "username": {"type": "string", "example": "city_hospital"},
                                "password": {"type": "string", "example": "hospital123"}
                            }
                        }
                    }
                ],
                "responses": {
                    "200": {"description": "Hospital login successful"},
                    "401": {"description": "Invalid hospital credentials"}
                }
            }
        },
        "/auth/profile": {
            "get": {
                "tags": ["Authentication"],
                "summary": "Get user profile",
                "description": "Retrieve current user's profile information",
                "security": [{"JWT": []}],
                "responses": {
                    "200": {
                        "description": "Profile retrieved successfully",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "success": {"type": "boolean", "example": True},
                                "data": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer", "example": 1},
                                        "username": {"type": "string", "example": "john_doe"},
                                        "email": {"type": "string", "example": "john@example.com"},
                                        "fullname": {"type": "string", "example": "John Doe"},
                                        "role": {"type": "string", "example": "user"}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "Unauthorized"}
                }
            }
        },
        # Hospital endpoints
        "/hospital/register": {
            "post": {
                "tags": ["Hospitals"],
                "summary": "Register a new hospital",
                "description": "Register a new hospital in the system",
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["username", "name", "type", "email", "password", "location", "reg_id"],
                            "properties": {
                                "username": {"type": "string", "example": "city_hospital"},
                                "name": {"type": "string", "example": "City General Hospital"},
                                "type": {"type": "string", "example": "General"},
                                "email": {"type": "string", "format": "email", "example": "admin@cityhospital.com"},
                                "password": {"type": "string", "example": "SecurePass123!"},
                                "location": {"type": "string", "example": "123 Main St, City, State"},
                                "reg_id": {"type": "string", "example": "REG123456"},
                                "is_multi_level": {"type": "boolean", "example": True}
                            }
                        }
                    }
                ],
                "responses": {
                    "201": {"description": "Hospital registered successfully"},
                    "400": {"description": "Invalid input data"},
                    "409": {"description": "Hospital already exists"}
                }
            }
        },
        "/hospital/all": {
            "get": {
                "tags": ["Hospitals"],
                "summary": "Get all hospitals",
                "description": "Retrieve a list of all registered hospitals",
                "parameters": [
                    {"name": "page", "in": "query", "type": "integer", "default": 1, "description": "Page number"},
                    {"name": "per_page", "in": "query", "type": "integer", "default": 10, "description": "Items per page"},
                    {"name": "search", "in": "query", "type": "string", "description": "Search term"}
                ],
                "responses": {
                    "200": {
                        "description": "Hospitals retrieved successfully",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "success": {"type": "boolean", "example": True},
                                "data": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer", "example": 1},
                                            "name": {"type": "string", "example": "City General Hospital"},
                                            "location": {"type": "string", "example": "123 Main St, City, State"},
                                            "contact_num": {"type": "string", "example": "+1234567890"},
                                            "hospital_type": {"type": "string", "example": "General"},
                                            "bedAvailability": {"type": "integer", "example": 50},
                                            "opd_status": {"type": "string", "example": "Open"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/hospital/{id}": {
            "get": {
                "tags": ["Hospitals"],
                "summary": "Get hospital by ID",
                "description": "Retrieve detailed information about a specific hospital",
                "parameters": [
                    {"name": "id", "in": "path", "type": "integer", "required": True, "description": "Hospital ID"}
                ],
                "responses": {
                    "200": {"description": "Hospital retrieved successfully"},
                    "404": {"description": "Hospital not found"}
                }
            },
            "put": {
                "tags": ["Hospitals"],
                "summary": "Update hospital",
                "description": "Update hospital information",
                "security": [{"JWT": []}],
                "parameters": [
                    {"name": "id", "in": "path", "type": "integer", "required": True, "description": "Hospital ID"},
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "example": "Updated Hospital Name"},
                                "location": {"type": "string", "example": "Updated Address"},
                                "contact_num": {"type": "string", "example": "+1234567890"},
                                "hospital_type": {"type": "string", "example": "Specialty"},
                                "bedAvailability": {"type": "integer", "example": 75},
                                "oxygenUnits": {"type": "integer", "example": 20}
                            }
                        }
                    }
                ],
                "responses": {
                    "200": {"description": "Hospital updated successfully"},
                    "404": {"description": "Hospital not found"},
                    "401": {"description": "Unauthorized"}
                }
            }
        },
        # Appointment endpoints
        "/appointment/opd/book": {
            "post": {
                "tags": ["Appointments"],
                "summary": "Book OPD appointment",
                "description": "Book an OPD appointment with a doctor",
                "security": [{"JWT": []}],
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["slot_id", "symptoms"],
                            "properties": {
                                "slot_id": {"type": "integer", "example": 1},
                                "symptoms": {"type": "string", "example": "Fever, headache"},
                                "notes": {"type": "string", "example": "Patient prefers morning appointment"}
                            }
                        }
                    }
                ],
                "responses": {
                    "201": {"description": "Appointment booked successfully"},
                    "400": {"description": "Invalid slot or input data"},
                    "401": {"description": "Unauthorized"}
                }
            }
        },
        "/appointment/my-appointments": {
            "get": {
                "tags": ["Appointments"],
                "summary": "Get user's appointments",
                "description": "Retrieve all appointments for the current user",
                "security": [{"JWT": []}],
                "parameters": [
                    {"name": "status", "in": "query", "type": "string", "enum": ["pending", "confirmed", "cancelled", "completed"], "description": "Filter by status"}
                ],
                "responses": {
                    "200": {"description": "Appointments retrieved successfully"},
                    "401": {"description": "Unauthorized"}
                }
            }
        },
        # Blood Bank endpoints
        "/bloodbank/register": {
            "post": {
                "tags": ["Blood Bank"],
                "summary": "Register blood bank",
                "description": "Register a new blood bank in the system",
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["name", "location", "contact_num", "email"],
                            "properties": {
                                "name": {"type": "string", "example": "City Blood Bank"},
                                "location": {"type": "string", "example": "456 Health Ave, City, State"},
                                "contact_num": {"type": "string", "example": "+1234567890"},
                                "email": {"type": "string", "format": "email", "example": "info@bloodbank.com"}
                            }
                        }
                    }
                ],
                "responses": {
                    "201": {"description": "Blood bank registered successfully"},
                    "400": {"description": "Invalid input data"}
                }
            }
        },
        "/bloodbank/request": {
            "post": {
                "tags": ["Blood Bank"],
                "summary": "Request blood",
                "description": "Request blood from blood bank",
                "security": [{"JWT": []}],
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["blood_type", "quantity", "urgency"],
                            "properties": {
                                "blood_type": {"type": "string", "enum": ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], "example": "O+"},
                                "quantity": {"type": "integer", "minimum": 1, "example": 2},
                                "urgency": {"type": "string", "enum": ["low", "medium", "high", "emergency"], "example": "high"},
                                "reason": {"type": "string", "example": "Surgery requirement"}
                            }
                        }
                    }
                ],
                "responses": {
                    "201": {"description": "Blood request submitted successfully"},
                    "400": {"description": "Invalid input data"},
                    "401": {"description": "Unauthorized"}
                }
            }
        },
        # Emergency endpoints
        "/emergency/call": {
            "post": {
                "tags": ["Emergency"],
                "summary": "Log emergency call",
                "description": "Log a new emergency call and request ambulance",
                "security": [{"JWT": []}],
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["location", "emergency_type", "severity"],
                            "properties": {
                                "location": {"type": "string", "example": "789 Emergency St, City, State"},
                                "emergency_type": {"type": "string", "example": "Accident"},
                                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"], "example": "high"},
                                "description": {"type": "string", "example": "Car accident with injuries"},
                                "patient_count": {"type": "integer", "minimum": 1, "example": 2}
                            }
                        }
                    }
                ],
                "responses": {
                    "201": {"description": "Emergency logged successfully"},
                    "400": {"description": "Invalid input data"},
                    "401": {"description": "Unauthorized"}
                }
            }
        },
        # User endpoints
        "/user/profile/update": {
            "put": {
                "tags": ["Users"],
                "summary": "Update user profile",
                "description": "Update current user's profile information",
                "security": [{"JWT": []}],
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "fullname": {"type": "string", "example": "John Updated Doe"},
                                "phone_num": {"type": "string", "example": "+1234567890"},
                                "location": {"type": "string", "example": "Updated Address"}
                            }
                        }
                    }
                ],
                "responses": {
                    "200": {"description": "Profile updated successfully"},
                    "400": {"description": "Invalid input data"},
                    "401": {"description": "Unauthorized"}
                }
            }
        },
        "/user/all": {
            "get": {
                "tags": ["Users"],
                "summary": "Get all users",
                "description": "Retrieve list of all users (Admin only)",
                "security": [{"JWT": []}],
                "parameters": [
                    {"name": "page", "in": "query", "type": "integer", "default": 1, "description": "Page number"},
                    {"name": "per_page", "in": "query", "type": "integer", "default": 10, "description": "Items per page"}
                ],
                "responses": {
                    "200": {"description": "Users retrieved successfully"},
                    "401": {"description": "Unauthorized"},
                    "403": {"description": "Forbidden - Admin only"}
                }
            }
        },
        # Admin endpoints
        "/admin/dashboard/stats": {
            "get": {
                "tags": ["Admin"],
                "summary": "Get dashboard statistics",
                "description": "Retrieve system statistics for admin dashboard",
                "security": [{"JWT": []}],
                "responses": {
                    "200": {
                        "description": "Statistics retrieved successfully",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "success": {"type": "boolean", "example": True},
                                "data": {
                                    "type": "object",
                                    "properties": {
                                        "total_users": {"type": "integer", "example": 150},
                                        "total_hospitals": {"type": "integer", "example": 25},
                                        "total_appointments": {"type": "integer", "example": 450},
                                        "active_emergencies": {"type": "integer", "example": 5}
                                    }
                                }
                            }
                        }
                    },
                    "401": {"description": "Unauthorized"},
                    "403": {"description": "Forbidden - Admin only"}
                }
            }
        },
        # Dashboard endpoints
        "/dashboard/": {
            "get": {
                "tags": ["Dashboard"],
                "summary": "Get user dashboard",
                "description": "Retrieve dashboard data for current user",
                "security": [{"JWT": []}],
                "responses": {
                    "200": {"description": "Dashboard data retrieved successfully"},
                    "401": {"description": "Unauthorized"}
                }
            }
        },
        # Notification endpoints
        "/notifications/": {
            "get": {
                "tags": ["Notifications"],
                "summary": "Get notifications",
                "description": "Retrieve notifications for current user",
                "security": [{"JWT": []}],
                "parameters": [
                    {"name": "unread_only", "in": "query", "type": "boolean", "description": "Get only unread notifications"}
                ],
                "responses": {
                    "200": {"description": "Notifications retrieved successfully"},
                    "401": {"description": "Unauthorized"}
                }
            }
        },
        "/notifications/send": {
            "post": {
                "tags": ["Notifications"],
                "summary": "Send notification",
                "description": "Send notification to user(s)",
                "security": [{"JWT": []}],
                "parameters": [
                    {
                        "name": "body",
                        "in": "body",
                        "required": True,
                        "schema": {
                            "type": "object",
                            "required": ["message", "recipient_id"],
                            "properties": {
                                "message": {"type": "string", "example": "Your appointment is confirmed"},
                                "recipient_id": {"type": "integer", "example": 1},
                                "type": {"type": "string", "enum": ["info", "warning", "error", "success"], "example": "info"}
                            }
                        }
                    }
                ],
                "responses": {
                    "201": {"description": "Notification sent successfully"},
                    "400": {"description": "Invalid input data"},
                    "401": {"description": "Unauthorized"}
                }
            }
        },
        # Audit endpoints
        "/audit/logs": {
            "get": {
                "tags": ["Audit"],
                "summary": "Get audit logs",
                "description": "Retrieve system audit logs (Admin only)",
                "security": [{"JWT": []}],
                "parameters": [
                    {"name": "page", "in": "query", "type": "integer", "default": 1, "description": "Page number"},
                    {"name": "action", "in": "query", "type": "string", "description": "Filter by action type"}
                ],
                "responses": {
                    "200": {"description": "Audit logs retrieved successfully"},
                    "401": {"description": "Unauthorized"},
                    "403": {"description": "Forbidden - Admin only"}
                }
            }
        }
    }