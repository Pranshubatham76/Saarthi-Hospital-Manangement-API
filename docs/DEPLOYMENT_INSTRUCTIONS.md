# Hospital Management System - Deployment Instructions

## Quick Fix for Current Error

The error you're encountering is because Gunicorn can't find the Flask app instance. Here's how to fix it:

### For Render/Heroku Deployment:

**Option 1: Use the new WSGI file (Recommended)**
```bash
gunicorn wsgi:app
```

**Option 2: Use the original run.py file**
```bash
gunicorn run:app
```

### Files Created/Updated:

1. **wsgi.py** - Main WSGI entry point for production
2. **Procfile** - Deployment configuration
3. **runtime.txt** - Python version specification
4. **render.yaml** - Render platform configuration

## Deployment Commands by Platform:

### Render
```yaml
# In render.yaml (already created)
startCommand: "gunicorn --bind 0.0.0.0:$PORT wsgi:app"
```

### Heroku
```bash
# In Procfile (already created)
web: gunicorn wsgi:app
```

### Railway
```bash
gunicorn wsgi:app --host 0.0.0.0 --port $PORT
```

### Digital Ocean App Platform
```yaml
run_command: gunicorn --worker-tmp-dir /dev/shm wsgi:app
```

## Environment Variables Required:

Set these in your deployment platform:

```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_URL=your-database-url
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your-admin-password
```

## Database Setup:

The `wsgi.py` file will automatically:
1. Create all database tables
2. Create default admin user
3. Create default ward categories

## Testing Locally:

1. **Test WSGI file:**
   ```bash
   python wsgi.py
   ```

2. **Test with Gunicorn:**
   ```bash
   gunicorn wsgi:app
   ```

3. **Test with original run.py:**
   ```bash
   gunicorn run:app
   ```

## Troubleshooting:

### If you still get "Failed to find attribute 'app'":
1. Make sure you're using `wsgi:app` not `app:app`
2. Check that wsgi.py is in your root directory
3. Verify that the app variable is properly defined in wsgi.py

### If database initialization fails:
1. Check your DATABASE_URL environment variable
2. Ensure database exists and is accessible
3. Check database permissions

### If imports fail:
1. Verify all required packages are in requirements.txt
2. Check Python version compatibility
3. Ensure all environment variables are set

## Quick Commands Summary:

**For immediate deployment fix:**
```bash
# Replace in your deployment configuration:
# OLD: gunicorn app:app
# NEW: gunicorn wsgi:app

# OR alternatively:
# NEW: gunicorn run:app
```

The key issue was that Gunicorn was looking for an 'app' attribute in the 'app' module, but your Flask app instance is created in run.py, not exposed in the app module itself.