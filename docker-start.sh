#!/bin/bash

# Script to start Docker containers for Natal Astrology Engine

# Make the script executable
chmod +x docker-start.sh

# Ensure .env file exists
if [ ! -f .env ]; then
  echo "Error: .env file not found. Please create it with your configuration."
  echo "You can copy from .env.example as a starting point."
  exit 1
fi

# Build and start the containers in detached mode
echo "Starting Docker containers..."
docker-compose up -d

# Show container status
echo "Container status:"
docker-compose ps

echo ""
echo "Application is running!"
echo "Web interface: http://localhost:5000"
echo "API: http://localhost:8000"
echo ""
echo "To view logs:"
echo "  All services: docker-compose logs -f"
echo "  Web only: docker-compose logs -f web"
echo "  API only: docker-compose logs -f api"
echo "  Redis only: docker-compose logs -f redis"
echo ""
echo "To stop containers: ./docker-stop.sh"