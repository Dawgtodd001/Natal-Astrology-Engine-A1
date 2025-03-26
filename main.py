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
            <title>Redirecting to API documentation</title>
        </head>
        <body>
            <h1>Redirecting...</h1>
            <p>The API is running on port 8000. Redirecting to the API documentation.</p>
            <p>If you are not redirected automatically, follow this <a href="http://localhost:8000/docs">link to the API documentation</a>.</p>
        </body>
    </html>
    """

# App that gunicorn can use (WSGI compatible)
app = flask_app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)