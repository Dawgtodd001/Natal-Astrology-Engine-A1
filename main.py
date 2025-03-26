"""
Main entry point for the Natal Astrology web interface and API
This file serves as a compatibility layer for gunicorn when started with main:app
and provides a user-friendly web interface for interacting with the API
"""
import os
import json
import requests
from urllib.parse import urljoin
from app.main import app as fastapi_app
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

# Create a Flask app as the web interface
app = Flask(__name__, 
            static_folder="static",
            template_folder="templates")

# Setup a secret key, required by sessions
app.secret_key = os.environ.get("SESSION_SECRET") or "natal_astrology_web_secret_key"

# Configuration
API_BASE_URL = os.environ.get("API_BASE_URL") or "http://localhost:8000"
API_KEY = os.environ.get("DEFAULT_API_KEY") or "test_key_1234567890"

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
    if request.method == 'POST':
        try:
            # Extract form data
            birth_data = {
                "birth_date": request.form.get('birth_date'),
                "birth_time": request.form.get('birth_time'),
                "latitude": float(request.form.get('latitude')),
                "longitude": float(request.form.get('longitude')),
                "house_system": request.form.get('house_system', 'placidus')
            }
            
            # Optional timezone field
            timezone = request.form.get('timezone')
            if timezone:
                birth_data["timezone"] = timezone
                
            # Make API request
            response = requests.post(
                urljoin(API_BASE_URL, '/api/chart'),
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                json=birth_data
            )
            
            if response.status_code == 200:
                chart_data = response.json()
                session['chart_data'] = chart_data
                session['birth_data'] = birth_data
                return render_template('chart_result.html', chart=chart_data, birth_data=birth_data)
            else:
                error_data = response.json()
                flash(f"Error: {error_data.get('detail', {}).get('message', 'Unknown error')}", 'danger')
                
        except Exception as e:
            flash(f"Error generating chart: {str(e)}", 'danger')
    
    # Get available house systems
    try:
        house_systems_response = requests.get(
            urljoin(API_BASE_URL, '/api/house-systems'),
            headers={"X-API-Key": API_KEY}
        )
        if house_systems_response.status_code == 200:
            house_systems = house_systems_response.json()
        else:
            house_systems = {"placidus": "Default house system"}
    except:
        house_systems = {"placidus": "Default house system"}
    
    return render_template('chart_form.html', house_systems=house_systems)

@app.route('/interpret', methods=['GET', 'POST'])
def interpret():
    """Chart interpretation page"""
    if request.method == 'POST':
        try:
            # Check if we're using existing chart data
            use_existing = request.form.get('use_existing') == 'true'
            
            if use_existing and 'birth_data' in session:
                # Use stored birth data
                birth_data = session['birth_data']
                birth_data["template_name"] = request.form.get('template_name', 'basic_text')
            else:
                # Extract new form data
                birth_data = {
                    "birth_date": request.form.get('birth_date'),
                    "birth_time": request.form.get('birth_time'),
                    "latitude": float(request.form.get('latitude')),
                    "longitude": float(request.form.get('longitude')),
                    "house_system": request.form.get('house_system', 'placidus'),
                    "template_name": request.form.get('template_name', 'basic_text')
                }
                
                # Optional timezone field
                timezone = request.form.get('timezone')
                if timezone:
                    birth_data["timezone"] = timezone
            
            # Make API request
            response = requests.post(
                urljoin(API_BASE_URL, '/api/interpret'),
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
                json=birth_data
            )
            
            if response.status_code == 200:
                interpretation = response.text
                return render_template('interpretation_result.html', 
                                      interpretation=interpretation, 
                                      birth_data=birth_data)
            else:
                error_data = response.json()
                flash(f"Error: {error_data.get('detail', {}).get('message', 'Unknown error')}", 'danger')
                
        except Exception as e:
            flash(f"Error generating interpretation: {str(e)}", 'danger')
    
    # Get available house systems
    try:
        house_systems_response = requests.get(
            urljoin(API_BASE_URL, '/api/house-systems'),
            headers={"X-API-Key": API_KEY}
        )
        if house_systems_response.status_code == 200:
            house_systems = house_systems_response.json()
        else:
            house_systems = {"placidus": "Default house system"}
    except:
        house_systems = {"placidus": "Default house system"}
    
    # Check if we have chart data in session
    has_chart = 'chart_data' in session and 'birth_data' in session
    
    return render_template('interpretation_form.html', 
                          house_systems=house_systems, 
                          has_chart=has_chart,
                          birth_data=session.get('birth_data', {}))

@app.route('/house-systems')
def house_systems():
    """Display information about house systems"""
    try:
        response = requests.get(
            urljoin(API_BASE_URL, '/api/house-systems'),
            headers={"X-API-Key": API_KEY}
        )
        if response.status_code == 200:
            systems = response.json()
            return render_template('house_systems.html', systems=systems)
        else:
            flash("Unable to retrieve house systems information", 'warning')
            return redirect(url_for('index'))
    except Exception as e:
        flash(f"Error: {str(e)}", 'danger')
        return redirect(url_for('index'))

@app.route('/api-redirect')
def api_redirect():
    """Redirect to the API documentation"""
    return redirect(f"{API_BASE_URL}/docs")

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