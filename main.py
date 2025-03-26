"""
Main entry point for the Natal Astrology API
This file serves as a compatibility layer for gunicorn when started with main:app
"""
from app.main import app as fastapi_app

# This allows gunicorn to load the FastAPI application correctly
# when using the command: gunicorn --bind 0.0.0.0:5000 main:app

# Create a WSGI app from the FastAPI app
from fastapi.middleware.wsgi import WSGIMiddleware

# Create a Flask app as a simple server for the default route
from flask import Flask
flask_app = Flask(__name__)

@flask_app.route('/')
def redirect_to_api():
    """Redirect users to the API documentation"""
    return """
    <html>
        <head>
            <meta http-equiv="refresh" content="0;url=http://localhost:8000/docs" />
            <title>Natal Astrology API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                .links {
                    margin-top: 20px;
                }
                .links a {
                    display: block;
                    margin-bottom: 10px;
                }
            </style>
        </head>
        <body>
            <h1>Natal Astrology API</h1>
            <p>Welcome to the Natal Astrology API service. The API is running on port 8000.</p>
            
            <div class="links">
                <h2>API Resources:</h2>
                <a href="http://localhost:8000/docs">Swagger Documentation</a>
                <a href="http://localhost:8000/redoc">ReDoc Documentation</a>
                <a href="http://localhost:8000/api/health">API Health Check</a>
            </div>
            
            <p>You are being redirected to the API documentation. If you are not redirected automatically, please click one of the links above.</p>
        </body>
    </html>
    """

# App that gunicorn can use (WSGI compatible)
app = flask_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)