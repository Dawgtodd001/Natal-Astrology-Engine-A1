# Chart Calculation Service - Implementation Plan

This document outlines the detailed implementation plan for extracting the Chart Calculation Service from the monolithic Natal Astrology Engine.

## Table of Contents

1. [Service Overview](#service-overview)
2. [API Design](#api-design)
3. [Code Extraction Strategy](#code-extraction-strategy)
4. [Database Design](#database-design)
5. [Caching Strategy](#caching-strategy)
6. [Deployment Configuration](#deployment-configuration)
7. [Testing Strategy](#testing-strategy)
8. [Integration Points](#integration-points)
9. [Implementation Steps](#implementation-steps)

## Service Overview

The Chart Calculation Service is responsible for performing astrological calculations including planetary positions, house systems, and aspects. It serves as the computational core of the Natal Astrology Engine.

### Functionality

- Generate complete natal charts
- Calculate planetary positions for any date/time/location
- Implement multiple house systems
- Calculate aspects between planets
- Calculate transits (planetary positions at a different time relative to a natal chart)
- Return structured chart data for further interpretation or display

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Chart Calculation Service                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────┐ │
│  │                 │    │                 │    │          │ │
│  │  API Layer      │    │  Calculation    │    │ Cache    │ │
│  │  (FastAPI)      │◄──►│  Engine         │◄──►│ Manager  │ │
│  │                 │    │                 │    │          │ │
│  └─────────────────┘    └─────────────────┘    └──────────┘ │
│                               │                      │      │
│                               ▼                      ▼      │
│                        ┌────────────┐         ┌───────────┐ │
│                        │            │         │           │ │
│                        │ Ephemeris  │         │  Redis    │ │
│                        │ Data       │         │  Cache    │ │
│                        │            │         │           │ │
│                        └────────────┘         └───────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                               │
                               ▼
                     ┌───────────────────┐
                     │                   │
                     │   PostgreSQL      │
                     │   Database        │
                     │                   │
                     └───────────────────┘
```

## API Design

### Endpoints

#### 1. Generate Natal Chart

```
POST /api/v1/charts/natal
```

**Request:**
```json
{
  "birth_date": "1990-01-15",
  "birth_time": "14:30",
  "latitude": 40.7128,
  "longitude": -74.0060,
  "timezone": "America/New_York",
  "house_system": "placidus",
  "zodiac_type": "tropical"
}
```

**Response:**
```json
{
  "chart_id": "c123456",
  "chart_type": "natal",
  "calculation_timestamp": "2025-03-27T15:30:45Z",
  "planets": [...],
  "houses": [...],
  "aspects": [...],
  "angles": {...}
}
```

#### 2. Calculate Transits

```
POST /api/v1/charts/transits
```

**Request:**
```json
{
  "birth_date": "1990-01-15",
  "birth_time": "14:30",
  "birth_latitude": 40.7128,
  "birth_longitude": -74.0060,
  "birth_timezone": "America/New_York",
  "transit_date": "2025-04-15",
  "transit_time": "12:00",
  "transit_latitude": 40.7128,
  "transit_longitude": -74.0060,
  "transit_timezone": "America/New_York",
  "house_system": "placidus",
  "zodiac_type": "tropical"
}
```

**Response:**
```json
{
  "transit_id": "t123456",
  "calculation_timestamp": "2025-03-27T15:30:45Z",
  "natal_chart": {...},
  "transit_chart": {...},
  "transit_aspects": [...]
}
```

#### 3. Get Available House Systems

```
GET /api/v1/house-systems
```

**Response:**
```json
{
  "house_systems": {
    "placidus": "Placidus house system (most commonly used)",
    "koch": "Koch house system",
    "equal": "Equal house system",
    "whole_sign": "Whole sign houses"
  }
}
```

#### 4. Health Check

```
GET /api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "database": "healthy",
    "redis": "healthy",
    "ephemeris_data": "healthy"
  },
  "calculation_engine": "operational"
}
```

### Authentication & Authorization

- API Key authentication required for all endpoints
- Rate limiting based on API key tier
- Source IP restrictions (optional)

## Code Extraction Strategy

### Current Code Structure

The calculation functionality is currently spread across multiple files:

- `app/core/charts.py` - Core chart generation
- `app/core/planets.py` - Planetary calculations
- `app/core/houses.py` - House system implementations
- `app/core/aspects.py` - Aspect calculations
- `app/core/transits.py` - Transit calculations
- `app/api/endpoints.py` - API endpoints handling calculation requests

### Extraction Approach

1. **Identify Dependencies**
   - Map all dependencies between calculation modules
   - Document external dependencies (libraries, data sources)

2. **Extract Core Calculation Modules**
   - Copy relevant calculation code to new service
   - Adjust imports and module structure
   - Ensure all calculations work independently

3. **Create Clean API Layer**
   - Define new API endpoints as specified above
   - Implement validation logic
   - Add authentication middleware

4. **Implement Caching**
   - Port existing Redis caching logic
   - Optimize cache keys and TTL strategies

5. **Add Database Integration**
   - Create tables for calculation history
   - Implement repository pattern for data access

## Database Design

### Tables

#### 1. Chart Calculations

Stores a record of each chart calculation:

```sql
CREATE TABLE chart_calculations (
    id SERIAL PRIMARY KEY,
    chart_id VARCHAR(64) UNIQUE NOT NULL,
    chart_type VARCHAR(20) NOT NULL,  -- 'natal', 'transit', etc.
    birth_date DATE NOT NULL,
    birth_time TIME NOT NULL,
    latitude NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL,
    timezone VARCHAR(50) NOT NULL,
    house_system VARCHAR(20) NOT NULL,
    zodiac_type VARCHAR(20) NOT NULL,
    calculation_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    api_key_id INTEGER,
    calculation_time_ms INTEGER,  -- performance metric
    cache_hit BOOLEAN DEFAULT FALSE
);
```

#### 2. Calculation Details

Optional storage of complete calculation results:

```sql
CREATE TABLE calculation_details (
    chart_id VARCHAR(64) PRIMARY KEY REFERENCES chart_calculations(chart_id),
    chart_data JSONB NOT NULL,  -- Full chart data
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Indexes

```sql
CREATE INDEX chart_calculations_birth_date_idx ON chart_calculations(birth_date);
CREATE INDEX chart_calculations_api_key_id_idx ON chart_calculations(api_key_id);
CREATE INDEX chart_calculations_calculation_timestamp_idx ON chart_calculations(calculation_timestamp);
```

## Caching Strategy

### Cache Keys

Design efficient cache keys for calculations:

```
natal:{birth_date}:{birth_time}:{latitude}:{longitude}:{timezone}:{house_system}:{zodiac_type}
```

```
transit:{birth_date}:{birth_time}:{birth_lat}:{birth_lng}:{birth_tz}:{transit_date}:{transit_time}:{transit_lat}:{transit_lng}:{transit_tz}:{house_system}:{zodiac_type}
```

### TTL Strategy

- Natal charts: 30 days (very stable data)
- Transit charts: 7 days (more frequently changing)
- Ephemeris data: 60 days (reference data)

### Cache Invalidation

No explicit invalidation needed due to TTL, but provide an admin endpoint for manual cache clearing if needed.

## Deployment Configuration

### Docker Configuration

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY . .

# Expose API port
EXPOSE 8000

# Run the service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Configuration

**Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: chart-calculation-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: chart-calculation-service
  template:
    metadata:
      labels:
        app: chart-calculation-service
    spec:
      containers:
      - name: chart-calculation-service
        image: natal-astrology/chart-calculation-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
```

**Service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: chart-calculation-service
spec:
  selector:
    app: chart-calculation-service
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

## Testing Strategy

### Unit Tests

- Test calculation functions in isolation
- Test validation logic
- Test caching layer with mocked Redis

### Integration Tests

- Test API endpoints with test database
- Test Redis integration
- Test performance with realistic data volumes

### Load Tests

- Measure performance under concurrent requests
- Establish baseline metrics for monitoring

## Integration Points

### Dependencies

- PostgreSQL database
- Redis cache
- Ephemeris data source (could be local files or external service)

### Consumers

- API Gateway
- Interpretation Service (for chart data)
- Web UI (potentially direct access in initial phases)

## Implementation Steps

### Phase 1: Initial Setup (Week 1)

1. Create new service repository
2. Set up FastAPI project structure
3. Implement database models and migration scripts
4. Set up Redis connection and caching utilities
5. Configure CI/CD pipeline

### Phase 2: Core Functionality (Weeks 2-3)

1. Extract and adapt chart calculation code
2. Implement new API endpoints
3. Add authentication middleware
4. Implement request/response validation
5. Add comprehensive error handling

### Phase 3: Caching & Optimization (Week 4)

1. Implement caching layer
2. Add performance monitoring
3. Optimize critical calculation paths
4. Set up logging and observability

### Phase 4: Testing & Documentation (Week 5)

1. Write unit and integration tests
2. Create API documentation
3. Perform performance benchmarking
4. Create operational runbook

### Phase 5: Deployment & Integration (Week 6)

1. Create Docker and Kubernetes configurations
2. Deploy to staging environment
3. Update API Gateway to route requests
4. Implement canary deployment strategy
5. Monitor and resolve any integration issues

## Metrics & Monitoring

Key metrics to track:

- Request rate by endpoint
- Calculation latency
- Cache hit/miss ratio
- Error rate by endpoint and type
- Database query latency
- Resource utilization (CPU, memory)

## Rollback Strategy

If issues arise during deployment:

1. Route traffic back to the monolithic application
2. Leave the service deployed but inactive
3. Fix issues in the service
4. Gradually reintroduce traffic when ready