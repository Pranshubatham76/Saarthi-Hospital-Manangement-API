from flask import Blueprint, render_template_string, jsonify, request
from app.utils.helpers import create_success_response

docs_bp = Blueprint('docs', __name__)

@docs_bp.route('/api-docs')
def api_docs():
    """Enhanced API Documentation and Testing Interface"""
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hospital Management System - API Documentation</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/themes/prism.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; background: #f5f7fa; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px 0; text-align: center; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .auth-section { background: white; border-radius: 10px; padding: 25px; margin-bottom: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .auth-section h2 { color: #333; margin-bottom: 20px; display: flex; align-items: center; }
        .auth-section h2 i { margin-right: 10px; color: #667eea; }
        .auth-form { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .auth-form input, .auth-form select, .auth-form button { padding: 12px; border: 2px solid #e1e5e9; border-radius: 6px; font-size: 14px; }
        .auth-form button { background: #667eea; color: white; border: none; cursor: pointer; transition: all 0.3s; }
        .auth-form button:hover { background: #5a67d8; transform: translateY(-2px); }
        .token-display { background: #f8f9fa; padding: 15px; border-radius: 6px; font-family: monospace; word-break: break-all; margin-top: 10px; }
        .endpoints-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 25px; }
        .endpoint-card { background: white; border-radius: 10px; padding: 25px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); transition: transform 0.3s; }
        .endpoint-card:hover { transform: translateY(-5px); }
        .endpoint-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
        .endpoint-method { padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; text-transform: uppercase; }
        .method-get { background: #e3f2fd; color: #1565c0; }
        .method-post { background: #e8f5e8; color: #2e7d32; }
        .method-put { background: #fff3e0; color: #ef6c00; }
        .method-delete { background: #ffebee; color: #c62828; }
        .endpoint-path { font-family: monospace; font-weight: bold; color: #333; }
        .endpoint-description { color: #666; margin-bottom: 20px; }
        .test-form { margin-top: 20px; }
        .test-form textarea, .test-form input { width: 100%; padding: 10px; border: 2px solid #e1e5e9; border-radius: 6px; margin-bottom: 10px; }
        .test-button { width: 100%; padding: 12px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; transition: all 0.3s; }
        .test-button:hover { background: #218838; }
        .response-area { margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 6px; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto; }
        .tabs { display: flex; border-bottom: 2px solid #e1e5e9; margin-bottom: 20px; }
        .tab { padding: 10px 20px; cursor: pointer; border: none; background: none; font-size: 14px; color: #666; transition: all 0.3s; }
        .tab.active { color: #667eea; border-bottom: 2px solid #667eea; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .status-indicator { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 10px; }
        .status-200 { background: #28a745; }
        .status-400 { background: #ffc107; }
        .status-500 { background: #dc3545; }
        .quick-actions { background: white; border-radius: 10px; padding: 25px; margin-bottom: 30px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .quick-actions h3 { margin-bottom: 15px; color: #333; }
        .quick-actions-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }
        .quick-action-btn { padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; text-align: center; transition: all 0.3s; }
        .quick-action-btn:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1><i class="fas fa-hospital"></i> Hospital Management System</h1>
            <p>Comprehensive API Documentation & Testing Interface</p>
        </div>
    </div>

    <div class="container">
        <!-- Authentication Section -->
        <div class="auth-section">
            <h2><i class="fas fa-key"></i> Authentication</h2>
            <p>Get your access token to test protected endpoints:</p>
            <div class="auth-form">
                <input type="email" id="loginEmail" placeholder="Email" value="admin">
                <input type="password" id="loginPassword" placeholder="Password" value="admin123">
                <select id="loginType">
                    <option value="admin">Admin Login</option>
                    <option value="user">User Login</option>
                    <option value="hospital">Hospital Login</option>
                </select>
            </div>
            <button class="test-button" onclick="authenticate()">
                <i class="fas fa-sign-in-alt"></i> Get Access Token
            </button>
            <div id="tokenDisplay" class="token-display" style="display: none;"></div>
        </div>

        <!-- Quick Actions -->
        <div class="quick-actions">
            <h3><i class="fas fa-bolt"></i> Quick Actions</h3>
            <div class="quick-actions-grid">
                <button class="quick-action-btn" onclick="testHealthCheck()">
                    <i class="fas fa-heartbeat"></i><br>Health Check
                </button>
                <button class="quick-action-btn" onclick="getSystemStats()">
                    <i class="fas fa-chart-bar"></i><br>System Stats
                </button>
                <button class="quick-action-btn" onclick="listHospitals()">
                    <i class="fas fa-hospital-alt"></i><br>List Hospitals
                </button>
                <button class="quick-action-btn" onclick="getMyProfile()">
                    <i class="fas fa-user"></i><br>My Profile
                </button>
            </div>
        </div>

        <!-- API Endpoints -->
        <div class="endpoints-grid" id="endpointsContainer">
            <!-- Endpoints will be dynamically loaded -->
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.24.1/plugins/autoloader/prism-autoloader.min.js"></script>
    <script>
        let currentToken = '';
        
        // API Endpoints Configuration
        const apiEndpoints = [
            {
                method: 'GET',
                path: '/health',
                description: 'Health check endpoint to verify API status',
                category: 'System',
                requiresAuth: false,
                exampleResponse: { success: true, status: 'healthy', database: 'connected' }
            },
            {
                method: 'POST',
                path: '/auth/register',
                description: 'Register a new user account',
                category: 'Authentication',
                requiresAuth: false,
                exampleBody: {
                    username: 'john_doe',
                    fullname: 'John Doe',
                    email: 'john@example.com',
                    password: 'SecurePass123!',
                    phone_num: '+1234567890',
                    location: 'New York, NY',
                    role: 'user'
                }
            },
            {
                method: 'POST',
                path: '/auth/login',
                description: 'Authenticate user and get access tokens',
                category: 'Authentication',
                requiresAuth: false,
                exampleBody: {
                    email: 'john@example.com',
                    password: 'SecurePass123!'
                }
            },
            {
                method: 'GET',
                path: '/auth/profile',
                description: 'Get current user profile information',
                category: 'Authentication',
                requiresAuth: true
            },
            {
                method: 'GET',
                path: '/hospital/all',
                description: 'Get list of all registered hospitals',
                category: 'Hospitals',
                requiresAuth: false,
                queryParams: ['page', 'per_page', 'search']
            },
            {
                method: 'POST',
                path: '/hospital/register',
                description: 'Register a new hospital in the system',
                category: 'Hospitals',
                requiresAuth: false,
                exampleBody: {
                    username: 'city_hospital',
                    name: 'City General Hospital',
                    type: 'General',
                    email: 'admin@cityhospital.com',
                    password: 'SecurePass123!',
                    location: '123 Main St, City, State',
                    reg_id: 'REG123456',
                    is_multi_level: true
                }
            },
            {
                method: 'GET',
                path: '/hospital/{id}',
                description: 'Get detailed hospital information by ID',
                category: 'Hospitals',
                requiresAuth: false,
                pathParams: ['id']
            },
            {
                method: 'POST',
                path: '/appointment/opd/book',
                description: 'Book an OPD appointment with a doctor',
                category: 'Appointments',
                requiresAuth: true,
                exampleBody: {
                    slot_id: 1,
                    symptoms: 'Fever, headache',
                    notes: 'Patient prefers morning appointment'
                }
            },
            {
                method: 'GET',
                path: '/appointment/my-appointments',
                description: 'Get all appointments for current user',
                category: 'Appointments',
                requiresAuth: true,
                queryParams: ['status']
            },
            {
                method: 'POST',
                path: '/bloodbank/register',
                description: 'Register a new blood bank',
                category: 'Blood Bank',
                requiresAuth: false,
                exampleBody: {
                    name: 'City Blood Bank',
                    location: '456 Health Ave, City, State',
                    contact_num: '+1234567890',
                    email: 'info@bloodbank.com'
                }
            },
            {
                method: 'POST',
                path: '/bloodbank/request',
                description: 'Request blood from blood bank',
                category: 'Blood Bank',
                requiresAuth: true,
                exampleBody: {
                    blood_type: 'O+',
                    quantity: 2,
                    urgency: 'high',
                    reason: 'Surgery requirement'
                }
            },
            {
                method: 'POST',
                path: '/emergency/call',
                description: 'Log emergency call and request ambulance',
                category: 'Emergency',
                requiresAuth: true,
                exampleBody: {
                    location: '789 Emergency St, City, State',
                    emergency_type: 'Accident',
                    severity: 'high',
                    description: 'Car accident with injuries',
                    patient_count: 2
                }
            },
            {
                method: 'GET',
                path: '/admin/dashboard/stats',
                description: 'Get system statistics for admin dashboard',
                category: 'Admin',
                requiresAuth: true
            }
        ];

        // Initialize the interface
        function initializeInterface() {
            renderEndpoints();
        }

        // Render all endpoints
        function renderEndpoints() {
            const container = document.getElementById('endpointsContainer');
            container.innerHTML = '';

            apiEndpoints.forEach((endpoint, index) => {
                const endpointCard = createEndpointCard(endpoint, index);
                container.appendChild(endpointCard);
            });
        }

        // Create endpoint card
        function createEndpointCard(endpoint, index) {
            const card = document.createElement('div');
            card.className = 'endpoint-card';
            
            const methodClass = `method-${endpoint.method.toLowerCase()}`;
            
            card.innerHTML = `
                <div class="endpoint-header">
                    <span class="endpoint-method ${methodClass}">${endpoint.method}</span>
                    <span class="endpoint-path">${endpoint.path}</span>
                </div>
                <p class="endpoint-description">${endpoint.description}</p>
                <div class="tabs">
                    <button class="tab active" onclick="switchTab(${index}, 'test')">Test</button>
                    <button class="tab" onclick="switchTab(${index}, 'example')">Example</button>
                    <button class="tab" onclick="switchTab(${index}, 'response')">Response</button>
                </div>
                <div id="tab-test-${index}" class="tab-content active">
                    ${createTestForm(endpoint, index)}
                </div>
                <div id="tab-example-${index}" class="tab-content">
                    ${createExampleContent(endpoint)}
                </div>
                <div id="tab-response-${index}" class="tab-content">
                    <div id="response-${index}" class="response-area">Response will appear here...</div>
                </div>
            `;
            
            return card;
        }

        // Create test form
        function createTestForm(endpoint, index) {
            let form = '<div class="test-form">';
            
            if (endpoint.pathParams) {
                endpoint.pathParams.forEach(param => {
                    form += `<input type="text" id="pathParam-${index}-${param}" placeholder="${param}" />`;
                });
            }
            
            if (endpoint.queryParams) {
                endpoint.queryParams.forEach(param => {
                    form += `<input type="text" id="queryParam-${index}-${param}" placeholder="${param} (query parameter)" />`;
                });
            }
            
            if (endpoint.exampleBody) {
                form += `<textarea id="requestBody-${index}" rows="8" placeholder="Request Body (JSON)">${JSON.stringify(endpoint.exampleBody, null, 2)}</textarea>`;
            }
            
            form += `<button class="test-button" onclick="testEndpoint(${index})">
                <i class="fas fa-play"></i> Test ${endpoint.method} ${endpoint.path}
            </button></div>`;
            
            return form;
        }

        // Create example content
        function createExampleContent(endpoint) {
            let content = '<h4>Request Example:</h4>';
            content += `<pre><code class="language-http">${endpoint.method} ${endpoint.path}`;
            
            if (endpoint.requiresAuth) {
                content += `\\nAuthorization: Bearer {your-token}`;
            }
            
            if (endpoint.exampleBody) {
                content += `\\nContent-Type: application/json\\n\\n${JSON.stringify(endpoint.exampleBody, null, 2)}`;
            }
            
            content += '</code></pre>';
            
            if (endpoint.exampleResponse) {
                content += '<h4>Response Example:</h4>';
                content += `<pre><code class="language-json">${JSON.stringify(endpoint.exampleResponse, null, 2)}</code></pre>`;
            }
            
            return content;
        }

        // Switch tabs
        function switchTab(endpointIndex, tabName) {
            // Remove active class from all tabs and contents
            const tabs = document.querySelectorAll(`#endpointsContainer .endpoint-card:nth-child(${endpointIndex + 1}) .tab`);
            const contents = document.querySelectorAll(`#endpointsContainer .endpoint-card:nth-child(${endpointIndex + 1}) .tab-content`);
            
            tabs.forEach(tab => tab.classList.remove('active'));
            contents.forEach(content => content.classList.remove('active'));
            
            // Add active class to selected tab and content
            event.target.classList.add('active');
            document.getElementById(`tab-${tabName}-${endpointIndex}`).classList.add('active');
        }

        // Authentication
        function authenticate() {
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const type = document.getElementById('loginType').value;
            
            let endpoint = '/auth/login';
            let body = { email, password };
            
            if (type === 'admin') {
                endpoint = '/auth/admin/login';
                body = { username: email, password };
            } else if (type === 'hospital') {
                endpoint = '/auth/hospital/login';
                body = { username: email, password };
            }
            
            makeRequest('POST', endpoint, body)
                .then(response => {
                    if (response.success && response.data.access_token) {
                        currentToken = response.data.access_token;
                        const tokenDisplay = document.getElementById('tokenDisplay');
                        tokenDisplay.innerHTML = `
                            <strong>Access Token:</strong><br>
                            <code>${currentToken}</code><br>
                            <small style="color: #28a745;">✓ Token saved automatically for protected endpoints</small>
                        `;
                        tokenDisplay.style.display = 'block';
                    }
                })
                .catch(error => {
                    console.error('Authentication failed:', error);
                    alert('Authentication failed. Please check your credentials.');
                });
        }

        // Test endpoint
        function testEndpoint(index) {
            const endpoint = apiEndpoints[index];
            let url = endpoint.path;
            
            // Handle path parameters
            if (endpoint.pathParams) {
                endpoint.pathParams.forEach(param => {
                    const value = document.getElementById(`pathParam-${index}-${param}`).value;
                    if (value) {
                        url = url.replace(`{${param}}`, value);
                    }
                });
            }
            
            // Handle query parameters
            const queryParams = [];
            if (endpoint.queryParams) {
                endpoint.queryParams.forEach(param => {
                    const input = document.getElementById(`queryParam-${index}-${param}`);
                    if (input && input.value) {
                        queryParams.push(`${param}=${encodeURIComponent(input.value)}`);
                    }
                });
            }
            
            if (queryParams.length > 0) {
                url += '?' + queryParams.join('&');
            }
            
            // Handle request body
            let body = null;
            if (endpoint.exampleBody) {
                const bodyInput = document.getElementById(`requestBody-${index}`);
                if (bodyInput && bodyInput.value.trim()) {
                    try {
                        body = JSON.parse(bodyInput.value);
                    } catch (e) {
                        alert('Invalid JSON in request body');
                        return;
                    }
                }
            }
            
            makeRequest(endpoint.method, url, body, endpoint.requiresAuth)
                .then(response => {
                    displayResponse(index, response, 200);
                })
                .catch(error => {
                    displayResponse(index, error, error.status || 500);
                });
        }

        // Make HTTP request
        function makeRequest(method, url, body = null, requiresAuth = false) {
            const headers = {
                'Content-Type': 'application/json'
            };
            
            if (requiresAuth && currentToken) {
                headers.Authorization = `Bearer ${currentToken}`;
            }
            
            const config = {
                method,
                headers
            };
            
            if (body && method !== 'GET') {
                config.body = JSON.stringify(body);
            }
            
            return fetch(url, config)
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(err => {
                            err.status = response.status;
                            throw err;
                        });
                    }
                    return response.json();
                });
        }

        // Display response
        function displayResponse(index, data, status) {
            const responseDiv = document.getElementById(`response-${index}`);
            const statusClass = status >= 200 && status < 300 ? 'status-200' : status >= 400 && status < 500 ? 'status-400' : 'status-500';
            
            responseDiv.innerHTML = `
                <div style="margin-bottom: 10px;">
                    <span class="status-indicator ${statusClass}"></span>
                    <strong>Status: ${status}</strong>
                </div>
                <pre><code class="language-json">${JSON.stringify(data, null, 2)}</code></pre>
            `;
            
            // Switch to response tab
            const endpointCard = responseDiv.closest('.endpoint-card');
            const tabs = endpointCard.querySelectorAll('.tab');
            const contents = endpointCard.querySelectorAll('.tab-content');
            
            tabs.forEach(tab => tab.classList.remove('active'));
            contents.forEach(content => content.classList.remove('active'));
            
            tabs[2].classList.add('active'); // Response tab
            contents[2].classList.add('active');
        }

        // Quick action functions
        function testHealthCheck() {
            makeRequest('GET', '/health')
                .then(response => alert(`Health Check: ${response.message}\\nStatus: ${response.data.status}`))
                .catch(error => alert('Health check failed'));
        }

        function getSystemStats() {
            makeRequest('GET', '/admin/dashboard/stats', null, true)
                .then(response => alert(`System Stats:\\n${JSON.stringify(response.data, null, 2)}`))
                .catch(error => alert('Failed to get system stats. Make sure you are authenticated as admin.'));
        }

        function listHospitals() {
            makeRequest('GET', '/hospital/all')
                .then(response => {
                    const hospitals = response.data;
                    alert(`Found ${hospitals.length} hospitals:\\n${hospitals.map(h => `• ${h.name} - ${h.location}`).join('\\n')}`);
                })
                .catch(error => alert('Failed to get hospitals list'));
        }

        function getMyProfile() {
            makeRequest('GET', '/auth/profile', null, true)
                .then(response => alert(`Your Profile:\\n${JSON.stringify(response.data, null, 2)}`))
                .catch(error => alert('Failed to get profile. Make sure you are authenticated.'));
        }

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', initializeInterface);
    </script>
</body>
</html>
    """)

@docs_bp.route('/api-test')
def api_test():
    """Simple API testing interface"""
    return create_success_response(
        'API Testing Interface Available',
        {
            'documentation_url': '/api-docs',
            'swagger_url': '/swagger',
            'swagger_json': '/swagger.json',
            'available_endpoints': {
                'authentication': [
                    'POST /auth/register',
                    'POST /auth/login',
                    'POST /auth/admin/login',
                    'POST /auth/hospital/login',
                    'GET /auth/profile'
                ],
                'hospitals': [
                    'POST /hospital/register',
                    'GET /hospital/all',
                    'GET /hospital/{id}',
                    'PUT /hospital/update/{id}'
                ],
                'appointments': [
                    'POST /appointment/opd/book',
                    'GET /appointment/my-appointments',
                    'GET /appointment/available-slots'
                ],
                'blood_bank': [
                    'POST /bloodbank/register',
                    'POST /bloodbank/request',
                    'GET /bloodbank/all'
                ],
                'emergency': [
                    'POST /emergency/call',
                    'GET /emergency/all',
                    'GET /emergency/ambulances/available'
                ],
                'admin': [
                    'GET /admin/dashboard/stats',
                    'POST /admin/create',
                    'GET /admin/logs'
                ]
            }
        }
    )