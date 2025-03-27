#!/bin/bash

# Script to set up the initial microservices directory structure
# This creates the directory skeleton, but does not move any files yet

# Create main directories
mkdir -p services/api-gateway/app/{core,middleware,models,routes}
mkdir -p services/chart-calculation/app/{core,api,models}
mkdir -p services/interpretation/app/{ai,templates,tasks,api}
mkdir -p services/user-profile/app/{api,models}
mkdir -p services/web-ui/app/{templates,static,routes}

mkdir -p shared/{config,monitoring,utils,models}
mkdir -p infra/{docker,kubernetes,monitoring/{prometheus,grafana}}
mkdir -p docs/{architecture,api,developer}
mkdir -p tests/{api-gateway,chart-calculation,interpretation,user-profile,web-ui}

# Create placeholder files for service entry points
touch services/api-gateway/app/main.py
touch services/chart-calculation/app/main.py
touch services/interpretation/app/main.py
touch services/user-profile/app/main.py
touch services/web-ui/app/main.py

# Create placeholder Dockerfiles for each service
cat > services/api-gateway/Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Copy shared code
COPY shared /app/shared

# Copy requirements file
COPY services/api-gateway/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/api-gateway /app/api-gateway

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8000

# Command to run the API Gateway
CMD ["python", "api-gateway/app/main.py"]
EOF

# Create similar placeholder Dockerfiles for other services
for service in chart-calculation interpretation user-profile web-ui; do
  sed "s/api-gateway/$service/g" services/api-gateway/Dockerfile > services/$service/Dockerfile
  
  # Create placeholder requirements.txt files
  touch services/$service/requirements.txt
done

# Create placeholder requirements.txt for API gateway
touch services/api-gateway/requirements.txt

# Create a placeholder docker-compose.yml file
cat > infra/docker/docker-compose.yml << EOF
version: '3.8'

services:
  # API Gateway
  api-gateway:
    build:
      context: ../..
      dockerfile: services/api-gateway/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ../../services/api-gateway:/app/api-gateway
      - ../../shared:/app/shared
    environment:
      - DATABASE_URL=\${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    networks:
      - astrology-network

  # Chart Calculation Service
  chart-calculation:
    build:
      context: ../..
      dockerfile: services/chart-calculation/Dockerfile
    ports:
      - "8001:8000"
    volumes:
      - ../../services/chart-calculation:/app/chart-calculation
      - ../../shared:/app/shared
    environment:
      - DATABASE_URL=\${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    networks:
      - astrology-network

  # Interpretation Service
  interpretation:
    build:
      context: ../..
      dockerfile: services/interpretation/Dockerfile
    ports:
      - "8002:8000"
    volumes:
      - ../../services/interpretation:/app/interpretation
      - ../../shared:/app/shared
    environment:
      - DATABASE_URL=\${DATABASE_URL}
      - REDIS_URL=redis://redis:6379/0
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
    depends_on:
      - redis
    networks:
      - astrology-network

  # User Profile Service
  user-profile:
    build:
      context: ../..
      dockerfile: services/user-profile/Dockerfile
    ports:
      - "8003:8000"
    volumes:
      - ../../services/user-profile:/app/user-profile
      - ../../shared:/app/shared
    environment:
      - DATABASE_URL=\${DATABASE_URL}
    networks:
      - astrology-network

  # Web UI Service
  web-ui:
    build:
      context: ../..
      dockerfile: services/web-ui/Dockerfile
    ports:
      - "5000:5000"
    volumes:
      - ../../services/web-ui:/app/web-ui
      - ../../shared:/app/shared
    environment:
      - API_GATEWAY_URL=http://api-gateway:8000
      - SESSION_SECRET=\${SESSION_SECRET}
    depends_on:
      - api-gateway
    networks:
      - astrology-network

  # Redis for caching and message broker
  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    networks:
      - astrology-network

  # Prometheus for metrics
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ../../infra/monitoring/prometheus:/etc/prometheus
      - prometheus-data:/prometheus
    networks:
      - astrology-network

  # Grafana for dashboards
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ../../infra/monitoring/grafana:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    networks:
      - astrology-network

volumes:
  redis-data:
  prometheus-data:
  grafana-data:

networks:
  astrology-network:
    driver: bridge
EOF

# Create README for the reorganization
cat > README_REORGANIZATION.md << EOF
# Microservices Reorganization

This directory structure has been created to facilitate the migration from a monolithic architecture to a microservices-based architecture.

## Structure Overview

- \`services/\`: Contains individual microservices
- \`shared/\`: Contains shared code used by multiple services
- \`infra/\`: Contains infrastructure configuration
- \`docs/\`: Contains documentation
- \`tests/\`: Contains tests for each service

## Next Steps

1. Move code from the existing monolith into the appropriate service directories
2. Update imports to reflect the new structure
3. Test each service independently
4. Update Docker and Kubernetes configurations as needed

See MICROSERVICES_REORGANIZATION.md for the complete migration plan.
EOF

echo "Microservices directory structure created successfully."
echo "Next step: Begin migrating code according to the plan in MICROSERVICES_REORGANIZATION.md"