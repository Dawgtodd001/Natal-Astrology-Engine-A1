# Deploying the Natal Astrology Engine on Replit

This guide provides instructions specifically for deploying the Natal Astrology Engine on Replit's platform.

## Pre-deployment Checklist

Before deploying, ensure the following:

1. **Database Configuration**:
   - Your PostgreSQL database is properly set up
   - The `DATABASE_URL` environment variable is correctly configured in the `.env` file

2. **Environment Variables**:
   - Verify all required environment variables are set in the `.env` file
   - For production, set `ENVIRONMENT=production`
   - Set a secure `SESSION_SECRET` for Flask session security
   - Set `API_BASE_URL=/api` for proper routing in Replit's environment

3. **Project Structure**:
   - The main Flask app is in `main.py`
   - The FastAPI backend is in `app/main.py`
   - Both apps can start independently using the provided workflows

## Deployment Steps

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

4. **Post-Deployment Verification**:
   - Check that the Flask frontend loads correctly
   - Verify the FastAPI backend is responding to requests
   - Test the geocoding functionality by looking up various locations
   - Generate a sample chart to confirm calculations work
   - Test timezone detection with different global locations

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

3. **Database Connection Errors**:
   - Verify your database credentials in the `.env` file
   - Check if your database provider allows connections from Replit's IP range
   - Test database connectivity with a basic query

4. **CORS/Origin Issues**:
   - Set `ALLOWED_ORIGINS` to include your Replit domain
   - For development, you can use `*` but restrict this in production

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