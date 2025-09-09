#!/usr/bin/env python3
"""
Route Discovery Script - Discovers all available routes in the Flask application
"""
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
import json

def discover_routes():
    """Discover all routes in the Flask application"""
    app = create_app()
    
    routes = []
    
    with app.app_context():
        for rule in app.url_map.iter_rules():
            # Skip static files and internal routes
            if rule.endpoint in ['static', 'admin.index', 'admin.static']:
                continue
                
            route_info = {
                'endpoint': rule.endpoint,
                'methods': list(rule.methods - {'HEAD', 'OPTIONS'}),  # Remove HEAD and OPTIONS
                'path': str(rule.rule),
                'blueprint': rule.endpoint.split('.')[0] if '.' in rule.endpoint else 'main'
            }
            
            # Determine if route likely requires authentication
            requires_auth = False
            if any(keyword in rule.endpoint.lower() for keyword in ['admin', 'dashboard', 'profile', 'my-', 'update']):
                requires_auth = True
            if 'login' in rule.endpoint.lower() or 'register' in rule.endpoint.lower() or 'health' in rule.endpoint.lower():
                requires_auth = False
                
            route_info['requires_auth'] = requires_auth
            
            routes.append(route_info)
    
    return routes

if __name__ == '__main__':
    try:
        routes = discover_routes()
        
        print("🔍 Discovered Routes:")
        print("=" * 50)
        
        # Group by blueprint
        blueprints = {}
        for route in routes:
            bp = route['blueprint']
            if bp not in blueprints:
                blueprints[bp] = []
            blueprints[bp].append(route)
        
        # Print routes organized by blueprint
        for blueprint, blueprint_routes in sorted(blueprints.items()):
            print(f"\n📁 {blueprint.upper()} Blueprint:")
            print("-" * 30)
            
            for route in sorted(blueprint_routes, key=lambda x: x['path']):
                methods_str = ', '.join(route['methods'])
                auth_indicator = "🔒" if route['requires_auth'] else "🔓"
                print(f"  {auth_indicator} {methods_str:15} {route['path']}")
        
        # Save to JSON file for Swagger generation
        with open('discovered_routes.json', 'w') as f:
            json.dump({
                'total_routes': len(routes),
                'blueprints': list(blueprints.keys()),
                'routes': routes
            }, f, indent=2)
        
        print(f"\n📊 Summary:")
        print(f"   Total Routes: {len(routes)}")
        print(f"   Blueprints: {len(blueprints)}")
        print(f"   Protected Routes: {sum(1 for r in routes if r['requires_auth'])}")
        print(f"   Public Routes: {sum(1 for r in routes if not r['requires_auth'])}")
        print(f"\n💾 Routes saved to 'discovered_routes.json'")
        
    except Exception as e:
        print(f"❌ Error discovering routes: {str(e)}")
        import traceback
        traceback.print_exc()