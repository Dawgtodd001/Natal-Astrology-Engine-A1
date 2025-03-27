# Microservices Reorganization Plan

This document outlines the plan for reorganizing the Natal Astrology Engine codebase from its current monolithic structure to a microservices-oriented directory structure.

## Proposed Directory Structure

```
/
├── services/                          # Parent directory for all microservices
│   ├── api-gateway/                   # API Gateway Service
│   │   ├── app/                       # Main application code
│   │   │   ├── core/                  # Core functionality
│   │   │   ├── middleware/            # Middleware components
│   │   │   ├── models/                # Data models
│   │   │   ├── routes/                # Route definitions
│   │   │   └── main.py                # Entry point
│   │   ├── Dockerfile                 # Service-specific Docker configuration
│   │   └── requirements.txt           # Service-specific dependencies
│   │
│   ├── chart-calculation/             # Chart Calculation Service
│   │   ├── app/                       # Main application code
│   │   │   ├── core/                  # Core calculation logic
│   │   │   ├── api/                   # API endpoints
│   │   │   ├── models/                # Data models
│   │   │   └── main.py                # Entry point
│   │   ├── Dockerfile                 # Service-specific Docker configuration
│   │   └── requirements.txt           # Service-specific dependencies
│   │
│   ├── interpretation/                # Interpretation Service
│   │   ├── app/                       # Main application code
│   │   │   ├── ai/                    # AI integration
│   │   │   ├── templates/             # Interpretation templates
│   │   │   ├── tasks/                 # Celery tasks
│   │   │   ├── api/                   # API endpoints
│   │   │   └── main.py                # Entry point
│   │   ├── Dockerfile                 # Service-specific Docker configuration
│   │   └── requirements.txt           # Service-specific dependencies
│   │
│   ├── user-profile/                  # User Profile Service
│   │   ├── app/                       # Main application code
│   │   │   ├── api/                   # API endpoints
│   │   │   ├── models/                # User data models
│   │   │   └── main.py                # Entry point
│   │   ├── Dockerfile                 # Service-specific Docker configuration
│   │   └── requirements.txt           # Service-specific dependencies
│   │
│   └── web-ui/                        # Web UI Service
│       ├── app/                       # Main application code
│       │   ├── templates/             # HTML templates
│       │   ├── static/                # Static assets
│       │   ├── routes/                # Route handlers
│       │   └── main.py                # Entry point
│       ├── Dockerfile                 # Service-specific Docker configuration
│       └── requirements.txt           # Service-specific dependencies
│
├── shared/                            # Shared code used by multiple services
│   ├── config/                        # Configuration utilities
│   ├── monitoring/                    # Monitoring utilities
│   ├── utils/                         # Common utility functions
│   └── models/                        # Shared data models
│
├── infra/                             # Infrastructure configuration
│   ├── docker/                        # Docker-related files
│   │   └── docker-compose.yml         # Main Docker Compose configuration
│   ├── kubernetes/                    # Kubernetes manifests
│   │   ├── api-gateway/               # API Gateway K8s manifests
│   │   ├── chart-calculation/         # Chart Calculation K8s manifests
│   │   └── ...                        # Other service manifests
│   └── monitoring/                    # Monitoring stack
│       ├── prometheus/                # Prometheus configuration
│       └── grafana/                   # Grafana dashboards and configuration
│
├── docs/                              # Documentation
│   ├── architecture/                  # Architecture documentation
│   ├── api/                           # API documentation
│   └── developer/                     # Developer guides
│
└── tests/                             # Tests
    ├── api-gateway/                   # API Gateway tests
    ├── chart-calculation/             # Chart Calculation tests
    └── ...                            # Other service tests
```

## Migration Strategy

### Phase 1: Preparation

1. Create the top-level directories for the new structure
2. Identify shared code that should be moved to the `shared` directory
3. Prepare configuration files for each service

### Phase 2: Service Extraction

For each service:

1. Create the service directory structure
2. Move service-specific code from the monolith
3. Adapt imports and dependencies
4. Create service-specific Dockerfile and requirements

### Phase 3: Documentation & Testing Updates

1. Update documentation to reflect the new structure
2. Reorganize tests to align with the services

## Code Movement Guide

### API Gateway

Move from `api_gateway/` to `services/api-gateway/`:
- `api_gateway/app/` → `services/api-gateway/app/`
- Update imports to use shared code where applicable

### Chart Calculation

Extract from existing code:
- `app/core/charts.py` → `services/chart-calculation/app/core/charts.py`
- `app/core/planets.py` → `services/chart-calculation/app/core/planets.py`
- `app/core/aspects.py` → `services/chart-calculation/app/core/aspects.py`
- `app/core/houses.py` → `services/chart-calculation/app/core/houses.py`
- `app/api/endpoints.py` (chart calculation endpoints) → `services/chart-calculation/app/api/endpoints.py`

### Interpretation Service

Extract from existing code:
- `app/ai/` → `services/interpretation/app/ai/`
- `app/tasks/` → `services/interpretation/app/tasks/`
- `app/api/endpoints.py` (interpretation endpoints) → `services/interpretation/app/api/endpoints.py`

### User Profile Service

Extract from existing code:
- `app/api/endpoints.py` (profile endpoints) → `services/user-profile/app/api/endpoints.py`
- `app/models.py` (UserProfile model) → `services/user-profile/app/models/user.py`

### Web UI Service

Extract from existing code:
- `main.py` (Flask app) → `services/web-ui/app/main.py`
- `templates/` → `services/web-ui/app/templates/`
- `static/` → `services/web-ui/app/static/`

### Shared Code

Move common code to the shared directory:
- `utils.py` → `shared/utils/common.py`
- `app/celery_app.py` → `shared/utils/celery_app.py`
- `monitoring.py` → `shared/monitoring/prometheus.py`
- Common models → `shared/models/`

## Dockerfile Updates

Service-specific Dockerfiles should:

1. Install shared code first
2. Install service-specific dependencies
3. Copy service code only
4. Set appropriate entry point and CMD

## Docker Compose Updates

Update `docker-compose.yml` to:

1. Use service-specific Dockerfiles
2. Mount shared code as volume for development
3. Configure appropriate service dependencies

## Next Steps After Reorganization

1. Update CI/CD pipeline to build and test individual services
2. Implement service discovery for inter-service communication
3. Deploy services independently to verify isolation
4. Create individual databases per service as needed
5. Implement event-based communication between services