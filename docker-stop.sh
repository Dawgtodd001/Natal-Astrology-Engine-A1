#!/bin/bash

# Script to stop Docker containers for Natal Astrology Engine

# Make the script executable
chmod +x docker-stop.sh

# Stop the containers
echo "Stopping Docker containers..."
docker-compose down

echo ""
echo "Containers stopped."
echo "To start again, run: ./docker-start.sh"