# API Gateway Service - Implementation Plan

This document outlines the detailed implementation plan for creating the API Gateway Service as part of the microservices migration for the Natal Astrology Engine.

## Table of Contents

1. [Service Overview](#service-overview)
2. [Gateway Design](#gateway-design)
3. [Routing Rules](#routing-rules)
4. [Authentication & Authorization](#authentication--authorization)
5. [Rate Limiting](#rate-limiting)
6. [Request/Response Transformation](#requestresponse-transformation)
7. [Service Discovery Integration](#service-discovery-integration)
8. [Deployment Configuration](#deployment-configuration)
9. [Implementation Steps](#implementation-steps)
10. [Testing Strategy](#testing-strategy)
11. [Monitoring & Observability](#monitoring--observability)

## Service Overview

The API Gateway Service acts as the entry point for all client requests to the Natal Astrology Engine microservices. It handles routing, authentication, rate limiting, and provides a unified API interface while hiding the complexity of the underlying service architecture.

### Functionality

- Route requests to appropriate microservices
- Authenticate and authorize requests
- Apply rate limiting and throttling
- Transform requests and responses
- Monitor and log API traffic
- Provide circuit breaking for resilience
- Load balance requests across service instances

### Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                      API Gateway Service                       │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐    ┌─────────────────┐    ┌───────────┐  │
│  │                 │    │                 │    │           │  │
│  │  Auth & Rate    │◄──►│  Routing        │◄──►│ Service   │  │
│  │  Limiting       │    │  Engine         │    │ Registry  │  │
│  │                 │    │                 │    │           │  │
│  └─────────────────┘    └─────────────────┘    └───────────┘  │
│                               │                                │
│                               ▼                                │
│                      ┌─────────────────┐                      │
│                      │                 │                      │
│                      │  API Analytics  │                      │
│                      │  & Monitoring   │                      │
│                      │                 │                      │
│                      └─────────────────┘                      │
│                                                               │
└───────────────────────────────────────────────────────────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
  ┌───────────────────┐┌──────────────────┐┌──────────────────┐
  │                   ││                  ││                  │
  │ Chart Calculation ││  Interpretation  ││  User Profile    │
  │ Service           ││  Service         ││  Service         │
  │                   ││                  ││                  │
  └───────────────────┘└──────────────────┘└──────────────────┘
```

## Gateway Design

### API Design Principles

- Maintain backward compatibility with existing API where possible
- Follow RESTful API design principles
- Use consistent error formats across all services
- Support both synchronous and asynchronous patterns
- Implement OpenAPI specification for documentation

### Technology Selection

We'll implement a custom API Gateway using FastAPI, leveraging its performance and async capabilities:

- **FastAPI** for the gateway implementation
- **Redis** for rate limiting and distributed state
- **PostgreSQL** for API key and configuration storage
- **Prometheus** for metrics collection

## Routing Rules

The gateway will use a routing table to direct requests to appropriate microservices:

| Path Pattern            | Destination Service      | Notes                         |
|-------------------------|--------------------------|-------------------------------|
| `/api/charts/*`         | Chart Calculation Service| Chart generation endpoints    |
| `/api/interpret/*`      | Interpretation Service   | Interpretation endpoints      |
| `/api/profiles/*`       | User Profile Service     | User profile management       |
| `/api/health`           | All services (aggregate) | Aggregated health check       |
| `/api/metrics`          | Monitoring Service       | Metrics collection            |
| `/api/tasks/*`          | Task status across services | Task status checking       |

### Implementation Strategy

Implement dynamic routing based on path patterns:

```python
async def route_request(request: Request):
    """Route the incoming request to the appropriate service."""
    path = request.url.path
    
    service = route_resolver.get_service_for_path(path)
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Forward the request to the service
    return await forward_request(request, service)
```

## Authentication & Authorization

### API Key Authentication

Maintain the existing API key authentication mechanism:

1. Extract API key from request header or query parameter
2. Validate API key against database
3. Apply rate limits based on API key tier
4. Track usage for billing/analytics

```python
async def validate_api_key(request: Request, db: Session = Depends(get_db)):
    """Validate API key from request."""
    api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key missing"
        )
    
    # Check if API key exists and is enabled
    db_key = await db.execute(
        select(ApiKey).where(ApiKey.key == api_key, ApiKey.enabled == True)
    ).scalar_one_or_none()
    
    if not db_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # Update last used timestamp
    db_key.last_used = datetime.utcnow()
    await db.commit()
    
    # Add API key info to request state for rate limiting
    request.state.api_key = db_key
    return db_key
```

### Future JWT Support

Design with the capability to add JWT authentication for user-specific actions:

```python
async def validate_jwt(request: Request):
    """Validate JWT token from request."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="JWT token missing"
        )
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(
            token, 
            secret_key, 
            algorithms=["HS256"]
        )
        request.state.user = payload
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid JWT token"
        )
```

## Rate Limiting

Implement a flexible rate limiting system:

### Redis-Based Implementation

```python
class RedisRateLimiter:
    """Redis-based rate limiter implementation."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """
        Check if request is within rate limit.
        
        Args:
            key: The rate limit key (e.g., "api_key:{key_id}")
            limit: Maximum number of requests allowed
            window: Time window in seconds
        
        Returns:
            bool: True if within limits, False otherwise
        """
        current = await self.redis.get(key) or 0
        if int(current) >= limit:
            return False
        
        pipeline = self.redis.pipeline()
        pipeline.incr(key)
        pipeline.expire(key, window)
        await pipeline.execute()
        return True
```

### Per-API Key Limits

```python
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting based on API key."""
    if hasattr(request.state, "api_key"):
        api_key = request.state.api_key
        
        # Get limits from API key record
        rate_limit = api_key.rate_limit
        daily_limit = api_key.daily_limit
        
        # Check rate limit (requests per minute)
        minute_key = f"rate_limit:minute:{api_key.id}:{int(time.time() / 60)}"
        if not await rate_limiter.check_rate_limit(minute_key, rate_limit, 60):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
        
        # Check daily limit
        day_key = f"rate_limit:day:{api_key.id}:{int(time.time() / 86400)}"
        if not await rate_limiter.check_rate_limit(day_key, daily_limit, 86400):
            raise HTTPException(
                status_code=429,
                detail="Daily limit exceeded"
            )
    
    # Continue processing request
    response = await call_next(request)
    return response
```

## Request/Response Transformation

### Request Transformation

1. Validate incoming requests
2. Add correlation IDs for tracing
3. Add request context (API key info, request time)

```python
async def preprocess_request(request: Request):
    """Preprocess and transform incoming request."""
    # Add correlation ID for request tracing
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    # Add timestamp for latency tracking
    request.state.start_time = time.time()
    
    # Create a new request with added headers
    modified_headers = dict(request.headers)
    modified_headers["X-Correlation-ID"] = correlation_id
    
    # Return modified request
    return request
```

### Response Transformation

1. Add standard headers
2. Format error responses consistently
3. Log response metrics

```python
async def postprocess_response(response: Response, request: Request):
    """Postprocess and transform outgoing response."""
    # Add correlation ID header to response
    if hasattr(request.state, "correlation_id"):
        response.headers["X-Correlation-ID"] = request.state.correlation_id
    
    # Add latency metrics
    if hasattr(request.state, "start_time"):
        latency = time.time() - request.state.start_time
        response.headers["X-Response-Time"] = str(latency)
    
    # Log response metrics
    logger.info(
        "API Request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency": latency if hasattr(request.state, "start_time") else None,
            "api_key_id": request.state.api_key.id if hasattr(request.state, "api_key") else None
        }
    )
    
    return response
```

## Service Discovery Integration

### Static Configuration (Initial Implementation)

Start with static service discovery via configuration:

```python
SERVICE_ROUTES = {
    "chart-calculation": {
        "url": "http://chart-calculation-service:8000",
        "health_check": "/api/v1/health",
        "paths": ["/api/charts/*", "/api/house-systems"]
    },
    "interpretation": {
        "url": "http://interpretation-service:8000",
        "health_check": "/api/v1/health",
        "paths": ["/api/interpret/*"]
    }
}
```

### Dynamic Service Discovery (Future Enhancement)

Plan for integration with Kubernetes or Consul for dynamic service discovery:

```python
class KubernetesServiceDiscovery:
    """Kubernetes-based service discovery."""
    
    def __init__(self, namespace="default"):
        self.namespace = namespace
        self.config = kubernetes.config.load_incluster_config()
        self.api = kubernetes.client.CoreV1Api()
        self.services = {}
        self.last_refresh = 0
    
    async def refresh_services(self):
        """Refresh services from Kubernetes API."""
        if time.time() - self.last_refresh < 30:  # Refresh every 30 seconds
            return
        
        services = self.api.list_namespaced_service(self.namespace)
        self.services = {
            s.metadata.name: {
                "url": f"http://{s.metadata.name}:{s.spec.ports[0].port}",
                "selector": s.spec.selector
            }
            for s in services.items
            if "app.kubernetes.io/component" in (s.metadata.labels or {})
            and s.metadata.labels["app.kubernetes.io/component"] == "microservice"
        }
        self.last_refresh = time.time()
    
    async def get_service_url(self, service_name):
        """Get URL for a service."""
        await self.refresh_services()
        if service_name in self.services:
            return self.services[service_name]["url"]
        return None
```

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
  name: api-gateway
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: natal-astrology/api-gateway:latest
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
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 20
```

**Service:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
spec:
  selector:
    app: api-gateway
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

**Ingress:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-gateway-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  rules:
  - host: api.natal-astrology.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 80
  tls:
  - hosts:
    - api.natal-astrology.com
    secretName: natal-astrology-tls
```

## Implementation Steps

### Phase 1: Initial Setup (Week 1)

1. Create new service repository
2. Set up FastAPI project structure
3. Implement database models for API keys
4. Set up Redis connection for rate limiting
5. Configure CI/CD pipeline

### Phase 2: Core Gateway Functionality (Weeks 2-3)

1. Implement static routing engine
2. Add API key authentication
3. Implement rate limiting middleware
4. Create request/response transformation logic
5. Add comprehensive logging

### Phase 3: Service Integration (Week 4)

1. Integrate with Chart Calculation Service
2. Add health check aggregation
3. Implement circuit breaker pattern
4. Add request timeout handling
5. Create service fallback mechanisms

### Phase 4: Testing & Documentation (Week 5)

1. Write unit and integration tests
2. Create API documentation with OpenAPI
3. Perform load testing
4. Create operational runbook

### Phase 5: Deployment & Monitoring (Week 6)

1. Create Docker and Kubernetes configurations
2. Deploy to staging environment
3. Set up monitoring dashboards
4. Implement canary deployment strategy
5. Monitor and resolve any issues

## Testing Strategy

### Unit Tests

- Test routing logic in isolation
- Test authentication and rate limiting
- Test request/response transformation

### Integration Tests

- Test routing to mock services
- Test authentication with test database
- Test rate limiting with Redis

### Load Tests

- Measure performance under concurrent requests
- Test rate limiting at scale
- Measure latency impact of the gateway

## Monitoring & Observability

### Metrics to Track

- Request count by path, method, and status code
- Request latency by service
- Error rate by service
- Rate limit rejections
- Authentication failures
- Circuit breaker trips
- Cache hit/miss ratio

### Health Check Endpoint

```
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "database": "healthy",
    "redis": "healthy"
  },
  "services": {
    "chart-calculation": "healthy",
    "interpretation": "healthy"
  }
}
```

### Logging Strategy

Use structured JSON logging with:

- Request details (method, path)
- Response details (status code, latency)
- User context (API key ID)
- Correlation ID for request tracing
- Error details for failures

```python
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log request and response details."""
    # Generate correlation ID
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    # Capture start time
    start_time = time.time()
    
    # Log request
    logger.info(
        "API Request Received",
        extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host,
            "user_agent": request.headers.get("User-Agent")
        }
    )
    
    try:
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            "API Response Sent",
            extra={
                "correlation_id": correlation_id,
                "status_code": response.status_code,
                "duration_ms": int(duration * 1000)
            }
        )
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        return response
        
    except Exception as e:
        # Log exception
        logger.error(
            "API Request Error",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000)
            },
            exc_info=True
        )
        raise
```

## Transition Strategy

1. Deploy API Gateway alongside existing monolith
2. Route a subset of requests to the gateway (e.g., new endpoints first)
3. Gradually increase traffic to the gateway
4. Monitor for errors and performance issues
5. Complete cutover once stable

## Rollback Strategy

If issues arise during deployment:

1. Route traffic back to the monolithic application
2. Fix issues in the gateway
3. Gradually reintroduce traffic when ready

## Security Considerations

- TLS termination at the gateway
- API key rotation capability
- DDoS protection
- OAuth integration (planned for future)
- Request validation to prevent injection attacks