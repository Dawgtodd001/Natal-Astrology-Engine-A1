# Natal Astrology API Setup Guide

This guide provides step-by-step instructions for setting up the Natal Astrology API on both development and production environments.

## Prerequisites

- Python 3.11 or later
- PostgreSQL database
- Pip (Python package manager)

## Environment Variables

The application uses the following environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| DATABASE_URL | PostgreSQL connection URL | None | Yes |
| ADMIN_PASSWORD | Password for admin endpoints | "natal_admin_2025" (dev only) | No |
| ENVIRONMENT | Environment type ("development" or "production") | "development" | No |
| ALLOWED_ORIGINS | Comma-separated list of allowed CORS origins | "*" | No |
| LOG_LEVEL | Logging level (INFO, DEBUG, etc.) | "INFO" | No |

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/natal-astrology-api.git
cd natal-astrology-api
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up the Database

Create a PostgreSQL database and set the `DATABASE_URL` environment variable:

```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/dbname"
```

On Windows:
```
set DATABASE_URL=postgresql://username:password@localhost:5432/dbname
```

### 5. Initialize the Database

The application will automatically create tables and seed initial data when first run.

## Running the Application

### Development Environment

```bash
# Start the API server with automatic reloading
python run.py

# Or use gunicorn for more robust serving
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

### Docker Environment (Recommended)

The project includes Docker configuration for easy setup and consistent environments:

1. Make sure Docker and Docker Compose are installed on your system:
   - [Docker Installation Guide](https://docs.docker.com/get-docker/)
   - [Docker Compose Installation Guide](https://docs.docker.com/compose/install/)

2. Configure environment variables:
   - Copy `.env.example` to `.env` and modify as needed
   - At minimum, configure your `DATABASE_URL`

3. Start the Docker environment:
   ```bash
   # Start all services
   ./docker-start.sh
   
   # The script will display URLs for accessing the web interface and API
   # Web interface: http://localhost:5000
   # API: http://localhost:8000
   
   # To view logs
   docker-compose logs -f
   
   # To stop all services
   ./docker-stop.sh
   ```

The Docker environment includes:
- Web interface (Flask) on port 5000
- API service (FastAPI) on port 8000
- Redis cache service
- Shared network for inter-service communication
- Volume for Redis persistence

### Production Environment

For production deployment, it's recommended to:

1. Set `ENVIRONMENT=production`
2. Set a secure `ADMIN_PASSWORD` or leave it unset to disable admin endpoints
3. Configure `ALLOWED_ORIGINS` with specific allowed domains
4. Use Docker with appropriate security settings (see Docker section above)
5. Configure a reverse proxy (like Nginx) for SSL termination

```bash
# Example production Docker deployment
export ENVIRONMENT=production
export ALLOWED_ORIGINS="https://yourdomain.com,https://admin.yourdomain.com"
docker-compose up -d
```

## API Key Management

API keys are required for almost all endpoints. The system automatically creates a default API key during first startup. To retrieve API keys:

1. Access the admin endpoint:
   - URL: `/api/admin/keys`
   - Query parameter: `admin_password` with the value from `ADMIN_PASSWORD` environment variable
   - In development mode, the default is "natal_admin_2025" if not set

2. The endpoint returns all API keys in the system.

## Testing

Run the included test scripts to verify functionality:

```bash
# Test the API endpoints
python test_api.py

# Test flatlib integration
python test_flatlib.py

# Test house system calculations
python test_house.py
```

## Troubleshooting

1. **Database connection issues**: Verify your PostgreSQL connection details and ensure the server is running.

2. **Import errors**: If you encounter import errors, check that all dependencies are installed correctly.

3. **Calculation errors**: Chart calculations require valid birth data (date, time, coordinates). Check your inputs if you're getting calculation errors.

4. **Performance issues**: Chart calculations can be computationally intensive. In production, consider enabling the caching mechanism by setting the appropriate environment variables.

5. **API key issues**: Make sure you're including the `X-API-Key` header in all requests. Verify the key exists and is enabled in the database.

## Additional Resources

- API Documentation: See `static/api_docs.md` or access `/docs` when the server is running
- Astrological Calculations: Based on the flatlib library
- PostgreSQL Documentation: https://www.postgresql.org/docs/