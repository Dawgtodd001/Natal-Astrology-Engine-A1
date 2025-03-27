#!/bin/bash

# This script sets up and runs Redis in a Docker container for the Natal Astrology Engine

# Check if Docker is available
if ! command -v docker &> /dev/null; then
  echo "Docker is required but not found. Please install Docker and try again."
  exit 1
fi

# Redis container name and port
CONTAINER_NAME="natal_astrology_redis"
REDIS_PORT=6379

# Check if the container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Redis container already exists. Checking if it's running..."
  
  # Check if the container is running
  if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Redis container is already running."
  else
    echo "Redis container exists but is not running. Starting it..."
    docker start ${CONTAINER_NAME}
    echo "Redis container started."
  fi
else
  # Create and run a new Redis container
  echo "Creating and starting Redis container..."
  docker run --name ${CONTAINER_NAME} -p ${REDIS_PORT}:6379 -d redis:alpine
  
  if [ $? -eq 0 ]; then
    echo "Redis container created and started successfully."
  else
    echo "Failed to create Redis container."
    exit 1
  fi
fi

# Display Redis connection information
echo "Redis is running on localhost:${REDIS_PORT}"
echo "Connection URL: redis://localhost:${REDIS_PORT}/0"
echo ""
echo "To view Redis logs, run: docker logs ${CONTAINER_NAME}"
echo "To stop Redis, run: docker stop ${CONTAINER_NAME}"
echo "To remove Redis container, run: docker rm -f ${CONTAINER_NAME}"