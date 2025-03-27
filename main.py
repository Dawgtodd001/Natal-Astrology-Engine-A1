"""
Main entry point for the Natal Astrology web interface and API
This file serves as a compatibility layer for gunicorn when started with main:app
and provides a user-friendly web interface for interacting with the API
"""
import os
import json
import logging
import requests
import threading
from urllib.parse import urljoin
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf.csrf import CSRFProtect, CSRFError
from shared.utils.api_client import check_api_health, api_request
from shared.monitoring.metrics import setup_metrics, track_api_request

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create a Flask app as the web interface
app = Flask(__name__, 
            static_folder="static",
            template_folder="templates")

# Setup a secret key, required by sessions
app.secret_key = os.environ.get("SESSION_SECRET") or "natal_astrology_web_secret_key"

# Secure session configuration
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') != 'development'  # Secure in production
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Provides CSRF protection for most cases
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # Session lifetime of 24 hours

# Setup CSRF protection
csrf = CSRFProtect(app)

# Setup Prometheus metrics
setup_metrics(app)

# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to response"""
    # Helps prevent XSS attacks
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Helps prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # Enable the XSS filter built into modern browsers
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Set Content Security Policy (CSP) with necessary exceptions for Bootstrap and other libraries
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "connect-src 'self'; "
    )
    response.headers['Content-Security-Policy'] = csp_policy
    return response

# CSRF error handler
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    return render_template('error.html', 
                          error_title="Security Error (CSRF)",
                          error_message="The form submission failed a security check. Please try again."), 400

# Generic error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html',
                          error_title="Page Not Found",
                          error_message="The page you requested could not be found."), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html',
                          error_title="Server Error",
                          error_message="An internal server error occurred. Please try again later."), 500

# Configuration
API_BASE_URL = os.environ.get("API_BASE_URL") or "http://localhost:8000"
API_KEY = os.environ.get("DEFAULT_API_KEY") or "test_key_1234567890"

# Global flag to track API availability
api_available = False

# Check API availability on startup and implement a retry mechanism
def check_api_availability():
    """
    Check if the FastAPI backend is available
    
    Implements a retry mechanism with exponential backoff
    """
    global api_available
    
    # Try to connect to the API with more retries and longer initial delay for startup
    if check_api_health(max_retries=8, initial_delay=2.0):
        app.logger.info("✅ API service is available")
        api_available = True
    else:
        app.logger.warning("⚠️ API service is not available. Some features may not work.")
        api_available = False
        
    return api_available

# Since Flask 2.0, before_first_request is removed, using a different approach
# Run the check after the app is created using with app.app_context()
with app.app_context():
    # Start in a background thread to avoid blocking app startup
    api_check_thread = threading.Thread(target=check_api_availability)
    api_check_thread.daemon = True  # Make thread exit when main thread exits
    api_check_thread.start()
    
# Add a middleware to check API availability before each request
@app.before_request
def ensure_api_availability():
    """
    Middleware to ensure API is available before processing certain requests
    Shows maintenance page if API is not available for chart-related pages
    """
    global api_available
    
    # List of routes that require the API to be available
    api_dependent_routes = ['/chart', '/interpret', '/profiles']
    
    # Check if we're accessing a route that needs the API
    if request.path in api_dependent_routes and not api_available:
        # If the API check was never successful, try again
        if check_api_availability():
            # If now available, proceed with the request
            return None
        
        # If still not available, show a maintenance page
        flash("The astrological calculation service is currently starting up. " +
              "Please try again in a few moments.", "warning")
        return render_template('maintenance.html', title="Service Starting"), 503
    
    # Proceed with the request normally
    return None

# Routes
@app.route('/')
def index():
    """Main page of the web interface"""
    return render_template('index.html')

@app.route('/api-docs')
def api_docs():
    """API documentation page"""
    return render_template('api_docs.html')

@app.route('/chart', methods=['GET', 'POST'])
def chart():
    """Chart generation page"""
    # Check if a profile is requested
    profile_id = request.args.get('profile')
    selected_profile = None
    
    if profile_id:
        try:
            # Get profiles from API with retry logic
            profiles = api_request('profiles', method="GET")
            
            if profiles:
                # Find the requested profile
                for profile in profiles:
                    if str(profile['id']) == profile_id:
                        selected_profile = profile
                        break
                
                if not selected_profile:
                    flash("Profile not found", "warning")
            else:
                flash("Unable to retrieve profile data. The server may be unavailable.", "warning")
                
        except Exception as e:
            flash(f"Error retrieving profile: {str(e)}", "danger")
    
    if request.method == 'POST':
        try:
            # Extract form data
            # Safely convert latitude and longitude to float with default values if missing
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            
            try:
                lat_float = float(latitude) if latitude else 0.0
                lng_float = float(longitude) if longitude else 0.0
            except (ValueError, TypeError):
                flash("Invalid latitude or longitude values. Please enter valid numbers.", "danger")
                return redirect(url_for('chart'))
            
            birth_data = {
                "birth_date": request.form.get('birth_date'),
                "birth_time": request.form.get('birth_time'),
                "latitude": lat_float,
                "longitude": lng_float,
                "house_system": request.form.get('house_system', 'placidus')
            }
            
            # Optional timezone field
            timezone = request.form.get('timezone')
            if timezone:
                birth_data["timezone"] = timezone
                
            # Check API health before making request
            if not check_api_health():
                flash("The API service is currently unavailable. Please try again later.", "danger")
                return redirect(url_for('chart'))
                
            # Make API request with retry logic
            app.logger.info("Making API request to /api/chart")
            chart_data = api_request('chart', data=birth_data)
            
            if chart_data:
                session['chart_data'] = chart_data
                session['birth_data'] = birth_data
                return render_template('chart_result.html', chart=chart_data, birth_data=birth_data)
            else:
                flash("Error generating chart. The server may be unavailable. Please try again later.", "danger")
                
        except Exception as e:
            flash(f"Error generating chart: {str(e)}", 'danger')
    
    # Get available house systems using our API request utility with retry logic
    house_systems = api_request('house-systems', method="GET") or {"placidus": "Default house system"}
    
    return render_template('chart_form.html', 
                          house_systems=house_systems,
                          profile=selected_profile)

@app.route('/interpret', methods=['GET', 'POST'])
def interpret():
    """Chart interpretation page"""
    if request.method == 'POST':
        try:
            # Check if we're using existing chart data
            use_existing = request.form.get('use_existing') == 'true'
            
            if use_existing and 'birth_data' in session:
                # Use stored birth data
                birth_data = session.get('birth_data', {})
                
                # Verify birth_data is a dictionary
                if not isinstance(birth_data, dict):
                    birth_data = {}
                    session['birth_data'] = birth_data
                    flash("Invalid chart data in session. Please generate a new chart.", "warning")
                    return redirect(url_for('chart'))
                
                # Add template name and AI options to the data
                birth_data["template_name"] = request.form.get('template_name', 'basic_text')
                birth_data["house_system"] = request.form.get('house_system', 'placidus')
                birth_data["use_ai"] = request.form.get('use_ai') == 'true'
                birth_data["ai_style"] = request.form.get('ai_style', 'detailed')
            else:
                # Extract new form data
                # Safely convert latitude and longitude to float with default values if missing
                latitude = request.form.get('latitude')
                longitude = request.form.get('longitude')
                
                try:
                    lat_float = float(latitude) if latitude else 0.0
                    lng_float = float(longitude) if longitude else 0.0
                except (ValueError, TypeError):
                    flash("Invalid latitude or longitude values. Please enter valid numbers.", "danger")
                    return redirect(url_for('interpret'))
                
                birth_data = {
                    "birth_date": request.form.get('birth_date'),
                    "birth_time": request.form.get('birth_time'),
                    "latitude": lat_float,
                    "longitude": lng_float,
                    "house_system": request.form.get('house_system', 'placidus'),
                    "template_name": request.form.get('template_name', 'basic_text'),
                    "use_ai": request.form.get('use_ai') == 'true',
                    "ai_style": request.form.get('ai_style', 'detailed')
                }
                
                # Optional timezone field
                timezone = request.form.get('timezone')
                if timezone:
                    birth_data["timezone"] = timezone
            
            # Make API request with enhanced error handling
            app.logger.info("Making API request to /api/interpret")
            response, error_info = api_request('interpret', data=birth_data, include_error_details=True, timeout=20)
            
            if response:
                # For interpretations, we expect plain text response
                interpretation = response
                
                # Explicitly log what we're passing to the template for debugging
                app.logger.info(f"Rendering interpretation with data type: {type(birth_data)}")
                
                # Render the template with the interpretation and birth data
                return render_template(
                    'interpretation_result.html', 
                    interpretation=interpretation, 
                    birth_data=birth_data
                )
            else:
                # Provide more specific error messages based on error details
                if error_info:
                    error_type = error_info.get("error_type", "Unknown")
                    error_message = error_info.get("error_message", "Unknown error")
                    
                    if error_type == "ServiceUnavailable":
                        flash("The astrology calculation service is currently starting up. Please try again in a few moments.", "warning")
                    elif error_type == "ConnectTimeout" or error_type == "ReadTimeout":
                        flash("The chart calculation is taking longer than expected. Complex calculations may need more time.", "warning")
                    elif error_type == "HTTPError" and error_info.get("status_code", 0) == 400:
                        flash(f"The birth information provided is invalid: {error_message}", "danger")
                    else:
                        # Log the detailed error for debugging
                        app.logger.error(f"API error: {error_type} - {error_message}")
                        flash("Error generating interpretation. The server reported a problem. Please check your input and try again later.", "danger")
                else:
                    flash("Error generating interpretation. The server may be unavailable. Please try again later.", "danger")
                
        except Exception as e:
            flash(f"Error generating interpretation: {str(e)}", 'danger')
    
    # Get available house systems using our API request utility with retry logic
    house_systems = api_request('house-systems', method="GET") or {"placidus": "Default house system"}
    
    # Check if we have chart data in session
    has_chart = 'chart_data' in session and 'birth_data' in session
    
    # Make sure birth_data is always a dictionary, not a list
    birth_data = session.get('birth_data', {})
    if not isinstance(birth_data, dict):
        birth_data = {}  # Reset to empty dict if it's not a dictionary
        session['birth_data'] = birth_data
        
    return render_template('interpretation_form.html', 
                          house_systems=house_systems, 
                          has_chart=has_chart,
                          birth_data=birth_data)

@app.route('/house-systems')
def house_systems():
    """Display information about house systems"""
    # Use our API request utility with enhanced error handling
    systems, error_info = api_request('house-systems', method="GET", include_error_details=True)
    
    if systems:
        return render_template('house_systems.html', systems=systems)
    else:
        # Provide more specific error messages based on error details
        if error_info:
            error_type = error_info.get("error_type", "Unknown")
            
            if error_type == "ServiceUnavailable":
                flash("The astrology service is currently starting up. Please try again in a few moments.", 'warning')
            else:
                app.logger.error(f"API error retrieving house systems: {error_type} - {error_info.get('error_message', 'Unknown error')}")
                flash("Unable to retrieve house systems information. The astrological calculation service encountered an error.", 'warning')
        else:
            flash("Unable to retrieve house systems information. The API may be unavailable.", 'warning')
            
        return redirect(url_for('index'))

@app.route('/cache-status')
def cache_status():
    """Display Redis cache status and statistics"""
    # Only admin can access this page
    admin_password = request.args.get("admin_password")
    
    if not admin_password:
        flash("Admin password is required to view cache status", "danger")
        return redirect(url_for('index'))
    
    # Pattern for filtering keys
    pattern = request.args.get("pattern", "astro_chart:*")
    
    # Check if Redis is available via health endpoint
    redis_available = False
    stats = {}
    keys = []
    
    try:
        # Check Redis health - use the existing api_request utility to ensure proper URL construction
        health_response, health_error = api_request("cache/health", method="GET", include_error_details=True)
        if health_response and not health_error:
            redis_available = health_response.get('available', False)
            
            if redis_available:
                # Get Redis stats
                stats, stats_error = api_request(
                    "cache/stats", 
                    data={"admin_password": admin_password}, 
                    method="GET", 
                    include_error_details=True
                )
                
                if stats_error:
                    flash(f"Error retrieving Redis stats: {stats_error.get('error_message', 'Unknown error')}", "danger")
                
                # Get Redis keys
                keys_params = {
                    "admin_password": admin_password,
                    "pattern": pattern,
                    "limit": 50
                }
                keys, keys_error = api_request("cache/keys", data=keys_params, method="GET", include_error_details=True)
                
                if keys_error:
                    flash(f"Error retrieving Redis keys: {keys_error.get('error_message', 'Unknown error')}", "danger")
    except Exception as e:
        app.logger.error(f"Error accessing cache endpoints: {str(e)}")
        flash(f"Error accessing cache: {str(e)}", "danger")
    
    return render_template(
        'cache_status.html',
        redis_available=redis_available,
        stats=stats,
        keys=keys,
        pattern=pattern,
        admin_password=admin_password
    )

@app.route('/flush-cache', methods=['POST'])
def flush_cache():
    """Flush Redis cache"""
    admin_password = request.form.get("admin_password")
    
    if not admin_password:
        flash("Admin password is required to flush cache", "danger")
        return redirect(url_for('index'))
    
    try:
        # Call flush endpoint with the api_request utility to ensure proper URL construction
        # Use DELETE method with the api_request utility
        result, error_info = api_request(
            "cache/flush", 
            data={"admin_password": admin_password}, 
            method="DELETE", 
            include_error_details=True
        )
        
        if result and not error_info:
            flash("Redis cache flushed successfully", "success")
        else:
            if error_info:
                flash(f"Error flushing Redis cache: {error_info.get('error_message', 'Unknown error')}", "danger")
            else:
                flash("Error flushing Redis cache: No response from server", "danger")
    except Exception as e:
        app.logger.error(f"Error flushing cache: {str(e)}")
        flash(f"Error flushing cache: {str(e)}", "danger")
    
    # Redirect back to cache status page
    return redirect(url_for('cache_status', admin_password=admin_password))

@app.route('/profiles')
def profiles():
    """Display user profiles"""
    # Use our API request utility with retry logic
    user_profiles = api_request('profiles', method="GET")
    
    if user_profiles:
        return render_template('profiles.html', profiles=user_profiles)
    else:
        flash("Unable to retrieve user profiles. The API may be unavailable.", 'warning')
        return redirect(url_for('index'))


@app.route('/profile/<int:profile_id>/edit', methods=['GET', 'POST'])
def edit_profile(profile_id):
    """Edit a user profile"""
    # Get profiles using our API request utility with retry logic
    profiles = api_request('profiles', method="GET")
    
    if not profiles:
        flash("Unable to retrieve profile data. The API may be unavailable.", 'warning')
        return redirect(url_for('profiles'))
    
    selected_profile = None
    
    # Find the requested profile
    for profile in profiles:
        if profile['id'] == profile_id:
            selected_profile = profile
            break
            
    if not selected_profile:
        flash("Profile not found", 'warning')
        return redirect(url_for('profiles'))
        
    # Handle form submission
    if request.method == 'POST':
        try:
            # Extract form data
            updated_profile = selected_profile.copy()
            updated_profile['name'] = request.form.get('name')
            updated_profile['birth_date'] = request.form.get('birth_date')
            updated_profile['birth_time'] = request.form.get('birth_time')
            
            # Safely convert latitude and longitude to float
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            
            try:
                updated_profile['latitude'] = float(latitude) if latitude else selected_profile['latitude']
                updated_profile['longitude'] = float(longitude) if longitude else selected_profile['longitude']
            except (ValueError, TypeError):
                flash("Invalid latitude or longitude values. Please enter valid numbers.", "danger")
                return redirect(url_for('edit_profile', profile_id=profile_id))
            
            updated_profile['timezone'] = request.form.get('timezone') or selected_profile['timezone']
            updated_profile['notes'] = request.form.get('notes') or selected_profile['notes']
            
            # Check API health before update
            if not check_api_health():
                flash("The API service is currently unavailable. Please try again later.", "danger")
                return redirect(url_for('edit_profile', profile_id=profile_id))
            
            # Update the profile via API with our custom endpoint name
            app.logger.info(f"Making API request to update profile {profile_id}")
            
            # Custom endpoint path for profile update
            update_endpoint = f"profiles/{profile_id}"
            result = api_request(update_endpoint, data=updated_profile, method="PUT")
            
            if result:
                flash("Profile updated successfully", 'success')
                return redirect(url_for('profiles'))
            else:
                flash("Failed to update profile. The server may be unavailable.", 'danger')
        
        except Exception as e:
            flash(f"Error updating profile: {str(e)}", 'danger')
    
    # Display edit form
    return render_template('edit_profile.html', profile=selected_profile)

@app.route('/api-redirect')
def api_redirect():
    """Redirect to the API documentation page that embeds API docs"""
    return redirect('/api-documentation')

@app.route('/api-documentation')
def api_documentation():
    """Embedded API documentation page"""
    # Create a page with an iframe that embeds the API docs within our Flask app
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Natal Astrology API Documentation</title>
        <link rel="stylesheet" href="/static/css/bootstrap-darkly.min.css">
        <style>
            body, html {
                height: 100%;
                margin: 0;
                padding: 0;
                overflow: hidden;
            }
            .header {
                background-color: #1a1a1a;
                color: white;
                padding: 15px;
                text-align: center;
                border-bottom: 1px solid #333;
            }
            .container-fluid {
                height: calc(100% - 60px);
                padding: 0;
            }
            iframe {
                width: 100%;
                height: 100%;
                border: none;
            }
            .back-button {
                margin: 10px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h2>Natal Astrology API Documentation</h2>
        </div>
        <a href="/" class="btn btn-secondary back-button">← Back to Home</a>
        <div class="container-fluid">
            <div class="content">
                <h3 class="p-3">API Endpoints</h3>
                <ul class="list-group m-3">
                    <li class="list-group-item">
                        <h5>1. Generate Chart</h5>
                        <p><strong>Endpoint:</strong> <code>/api/chart</code></p>
                        <p><strong>Method:</strong> POST</p>
                        <p><strong>Description:</strong> Generate a complete natal chart based on birth information</p>
                    </li>
                    <li class="list-group-item">
                        <h5>2. Chart Interpretation</h5>
                        <p><strong>Endpoint:</strong> <code>/api/interpret</code></p>
                        <p><strong>Method:</strong> POST</p>
                        <p><strong>Description:</strong> Generate an interpretation of a natal chart</p>
                    </li>
                    <li class="list-group-item">
                        <h5>3. House Systems</h5>
                        <p><strong>Endpoint:</strong> <code>/api/house-systems</code></p>
                        <p><strong>Method:</strong> GET</p>
                        <p><strong>Description:</strong> Get information about available house systems</p>
                    </li>
                    <li class="list-group-item">
                        <h5>4. Transits</h5>
                        <p><strong>Endpoint:</strong> <code>/api/transits</code></p>
                        <p><strong>Method:</strong> POST</p>
                        <p><strong>Description:</strong> Calculate transit chart and transit-to-natal aspects</p>
                    </li>
                    <li class="list-group-item">
                        <h5>5. User Profiles</h5>
                        <p><strong>Endpoint:</strong> <code>/api/profiles</code></p>
                        <p><strong>Method:</strong> GET</p>
                        <p><strong>Description:</strong> Get all user profiles</p>
                    </li>
                    <li class="list-group-item">
                        <h5>6. Update User Profile</h5>
                        <p><strong>Endpoint:</strong> <code>/api/profiles/{profile_id}</code></p>
                        <p><strong>Method:</strong> PUT</p>
                        <p><strong>Description:</strong> Update a user profile</p>
                    </li>
                    <li class="list-group-item">
                        <h5>7. Health Check</h5>
                        <p><strong>Endpoint:</strong> <code>/api/health</code></p>
                        <p><strong>Method:</strong> GET</p>
                        <p><strong>Description:</strong> Check the health status of the API</p>
                    </li>
                </ul>
                <div class="m-3">
                    <h3>API Usage</h3>
                    <p>All API requests require an API key provided in the header:</p>
                    <pre><code>X-API-Key: your_api_key_here</code></pre>
                </div>
            </div>
        </div>
        <script src="/static/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    '''

# Run the FastAPI application on a different port
if __name__ == "__main__":
    import threading
    import uvicorn
    
    # Start the FastAPI app in a separate thread
    def run_fastapi():
        uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)
    
    api_thread = threading.Thread(target=run_fastapi)
    api_thread.daemon = True
    api_thread.start()
    
    # Run the Flask web interface
    app.run(host="0.0.0.0", port=5000, debug=True)