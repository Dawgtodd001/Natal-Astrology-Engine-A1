# Deploying the Natal Astrology Engine on Replit

This guide provides instructions specifically for deploying the Natal Astrology Engine on Replit's platform.

## Pre-deployment Checklist

Before deploying, ensure the following:

1. **Database Configuration**:
   - Your PostgreSQL database is properly set up on Replit (or use an external database)
   - The `DATABASE_URL` environment variable is correctly configured in Replit Secrets or `.env` file
   - Database tables have been initialized properly with seed data

2. **Environment Variables**:
   - Verify all required environment variables are set in the `.env` file or Replit Secrets:
     - `SESSION_SECRET` (required): A secure random string for Flask session encryption
     - `DEFAULT_API_KEY` (required): The API key used for internal communication between Flask and FastAPI
     - `ENVIRONMENT=production` (recommended): Sets production mode with additional security checks
     - `API_BASE_URL=/api` (required): For proper routing in Replit's deployment environment
     - `OPENAI_API_KEY` (optional): Required only if using AI-powered interpretations

3. **Project Structure**:
   - The main Flask app is in `main.py` at the root directory
   - The FastAPI backend is in `app/main.py`
   - Static files are in the `static` directory
   - Templates are in the `templates` directory
   - Both apps are configured to start using the provided workflows

4. **API Health Check**:
   - The enhanced API health check with exponential backoff is implemented
   - The maintenance page template (`templates/maintenance.html`) exists
   - The Flask middleware to check API availability before processing requests is active

## Deployment Steps

### Option 1: Standard Replit Deployment

1. **Set Up Replit Secrets (if needed)**:
   - If using OpenAI for interpretations, add your `OPENAI_API_KEY` as a secret
   - Add any other sensitive credentials as secrets

2. **Configure the Procfile**:
   - The Procfile should already be set up with the following commands:
   ```
   web: gunicorn --workers 4 --bind 0.0.0.0:5000 main:app
   api: uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. **Deploy Your Application**:
   - Use the Replit deployment interface to deploy your application
   - Make sure both web and API services are running
   - The Flask frontend should be accessible at the root URL
   - The FastAPI backend should be accessible at /api

### Option 2: Docker Deployment

For better isolation and environment consistency, you can use Docker deployment:

1. **Set Up Environment Variables**:
   - Create a `.env` file based on `.env.example`
   - Add your database credentials, API keys, and other configuration

2. **Build and Deploy Docker Containers**:
   - Make sure Docker and Docker Compose are installed on your deployment server
   - Run the provided scripts to start the Docker environment:
   ```bash
   # Start all services
   ./docker-start.sh
   
   # Monitor logs
   docker-compose logs -f
   ```

3. **Configure for Production**:
   - Set `ENVIRONMENT=production` in your `.env` file
   - Set `ALLOWED_ORIGINS` to your specific domain(s)
   - Consider using a reverse proxy like Nginx for SSL termination

### Post-Deployment Verification

Regardless of deployment method, verify your application:

1. **Check that the Flask frontend loads correctly**
2. **Verify the FastAPI backend is responding to requests**
3. **Test the geocoding functionality by looking up various locations**
4. **Generate a sample chart to confirm calculations work**
5. **Test timezone detection with different global locations**
6. **Verify that Redis caching is working properly (if enabled)**

## Troubleshooting

### Common Issues and Solutions

1. **"Web server is unreachable" Error**:
   - Check if both workflows (Flask and FastAPI) are running
   - Verify port bindings are correct (5000 for Flask, 8000 for FastAPI)
   - Ensure Flask is using `0.0.0.0` as the host, not `localhost`

2. **API Connection Issues**:
   - Verify the `API_BASE_URL` is correctly set to `/api`
   - Check that API health checks are passing in the logs
   - Confirm the FastAPI service is running and accessible
   - Look for the "API service is available" success message in logs
   - If you see the maintenance page, wait for the health check to complete

3. **Database Connection Errors**:
   - Verify your database credentials in the `.env` file
   - Check if your database provider allows connections from Replit's IP range
   - Test database connectivity with a basic query
   - Ensure database tables are created properly

4. **CORS/Origin Issues**:
   - Set `ALLOWED_ORIGINS` to include your Replit domain
   - For development, you can use `*` but restrict this in production

5. **Maintenance Page Appears**:
   - This is normal during initial startup while the FastAPI backend initializes
   - The page will auto-refresh every 10 seconds until the API is available
   - If it persists for more than a minute, check the FastAPI logs for errors

6. **API Health Check Failures**:
   - The application implements an enhanced health check with exponential backoff
   - Check logs for specific error messages in the API health check
   - Verify that both workflows (Flask and FastAPI) started successfully
   - If health checks consistently fail, restart both workflows

### Docker-Specific Issues

7. **Docker Services Not Starting**:
   - Verify Docker and Docker Compose are installed and running
   - Check Docker logs with `docker-compose logs -f`
   - Ensure all required environment variables are set in your `.env` file
   - Make sure ports 5000, 8000, and 6379 are available and not in use by other services

8. **Redis Connection Issues in Docker**:
   - Verify Redis service is running: `docker-compose ps redis`
   - Check Redis logs: `docker-compose logs redis`
   - Make sure the `REDIS_URL` in your `.env` file is set to `redis://redis:6379/0`
   - The Redis container name must match the hostname in the Redis URL

9. **Container Networking Problems**:
   - Services must be on the same Docker network to communicate
   - Verify network settings in `docker-compose.yml`
   - Try accessing services using Docker service names instead of localhost

10. **Docker Volume Persistence**:
    - Redis data is stored in a Docker volume
    - Make sure the volume is properly defined in `docker-compose.yml`
    - If Redis data is not persisting, check volume mount configuration

## Scaling Considerations

For production use with higher traffic:

1. **Database Optimization**:
   - Enable the built-in caching mechanism for chart calculations
   - Consider database connection pooling settings

2. **Performance Tuning**:
   - Adjust the number of Gunicorn workers based on your Replit plan
   - Enable response compression if needed

3. **Security Hardening**:
   - Restrict admin endpoints
   - Use rate limiting to prevent abuse
   - Apply detailed API key permissions

## Support

If you encounter issues specific to Replit deployment:
- Check the Replit documentation on deployments
- Review your application logs for error messages
- Consider reaching out to Replit support for platform-specific questions