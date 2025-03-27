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
from app.main import app as fastapi_app
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_wtf.csrf import CSRFProtect, CSRFError
from utils import check_api_health, api_request

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

# Check API availability on startup
def check_api_availability():
    """Check if the FastAPI backend is available"""
    if check_api_health():
        app.logger.info("API service is available")
    else:
        app.logger.warning("API service is not available. Some features may not work.")

# Since Flask 2.0, before_first_request is removed, using a different approach
# Run the check after the app is created using with app.app_context()
with app.app_context():
    threading.Thread(target=check_api_availability).start()

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
            
            # Check API health before making request
            if not check_api_health():
                flash("The API service is currently unavailable. Please try again later.", "danger")
                return redirect(url_for('interpret'))
                
            # Make API request with retry logic
            app.logger.info("Making API request to /api/interpret")
            response = api_request('interpret', data=birth_data)
            
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
    # Use our API request utility with retry logic
    systems = api_request('house-systems', method="GET")
    
    if systems:
        return render_template('house_systems.html', systems=systems)
    else:
        flash("Unable to retrieve house systems information. The API may be unavailable.", 'warning')
        return redirect(url_for('index'))

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
    """Redirect to the API documentation"""
    # In Replit environment, we need to use relative paths 
    # or the user's actual browser URL rather than localhost
    
    # For Replit, this will be a path-relative URL to the docs page
    # Make sure this URL matches the FastAPI docs configuration
    docs_url = "/api/docs"
    
    return redirect(docs_url)

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