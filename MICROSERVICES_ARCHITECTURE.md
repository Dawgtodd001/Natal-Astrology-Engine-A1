# Natal Astrology Engine - Microservices Architecture

This document outlines the migration strategy from the current monolithic architecture to a microservices-based architecture for the Natal Astrology Engine.

## Repository Overview

This repository contains the documentation and implementation plans for transforming the Natal Astrology Engine from a monolithic architecture to a microservices architecture.

The Natal Astrology Engine is being redesigned as a microservices-based system to improve:

- **Scalability**: Independent scaling of components based on demand
- **Maintainability**: Smaller, focused codebases for each service
- **Development Velocity**: Parallel development of services
- **Resilience**: Isolated failures that don't affect the entire system
- **Technology Flexibility**: Different technologies for different services when appropriate

## Documentation Index

### 1. Architecture and Strategy

- [**MICROSERVICES_ARCHITECTURE.md**](./MICROSERVICES_ARCHITECTURE.md) - (This document) Comprehensive overview of the microservices architecture, including service definitions, communication patterns, data management strategies, and the overall migration roadmap.

- [**MICROSERVICES_IMPLEMENTATION_TIMELINE.md**](./MICROSERVICES_IMPLEMENTATION_TIMELINE.md) - Detailed 6-month implementation plan with phased approach, resource requirements, and success metrics for the transformation.

### 2. Service Implementation Plans

- [**CHART_CALCULATION_SERVICE.md**](./CHART_CALCULATION_SERVICE.md) - Detailed implementation plan for the Chart Calculation Service, the first microservice to be extracted from the monolith.

- [**API_GATEWAY_SERVICE.md**](./API_GATEWAY_SERVICE.md) - Implementation plan for the API Gateway Service, which will facilitate the transition from monolith to microservices and handle cross-cutting concerns.

### 3. CI/CD and DevOps

- [**CI_CD_PIPELINE.md**](./CI_CD_PIPELINE.md) - Complete continuous integration and continuous deployment pipeline design for automating the building, testing, and deployment of microservices.

## Table of Contents

1. [Current Architecture](#current-architecture)
2. [Microservices Architecture Overview](#microservices-architecture-overview)
3. [Service Definitions](#service-definitions)
4. [Communication Patterns](#communication-patterns)
5. [Data Management](#data-management)
6. [Deployment Strategy](#deployment-strategy)
7. [Migration Roadmap](#migration-roadmap)
8. [Technology Stack](#technology-stack)
9. [Observability & Monitoring](#observability--monitoring)
10. [Security Considerations](#security-considerations)
11. [Implementation Approach](#implementation-approach)
12. [Migration Status](#migration-status)

## Current Architecture

The Natal Astrology Engine currently operates as a monolithic application with the following components:

- **Web Interface (Flask)**: User-facing web application
- **API Layer (FastAPI)**: RESTful API for astrological calculations
- **Chart Calculation Engine**: Core astrological computation logic
- **AI Integration**: OpenAI-powered chart interpretations
- **Data Storage**: PostgreSQL database for persistent storage
- **Caching**: Redis for computation caching and task queuing
- **Async Processing**: Celery for handling heavy computational tasks
- **Monitoring**: Prometheus/Grafana for system observability

## Microservices Architecture Overview

The proposed microservices architecture breaks down the monolith into the following services:

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│                  │     │                  │     │                  │
│    Web UI        │     │   API Gateway    │     │  Monitoring &    │
│    Service       │     │   Service        │     │  Metrics Service │
│                  │     │                  │     │                  │
└────────┬─────────┘     └───────┬──────────┘     └─────────┬────────┘
         │                       │                          │
         │                       │                          │
         │                       ▼                          │
         │            ┌──────────────────────┐             │
         │            │                      │             │
         └────────────►  Service Registry    ◄─────────────┘
                      │                      │
                      └──────────┬───────────┘
                                 │
                ┌────────────────┼─────────────────┐
                │                │                 │
                ▼                ▼                 ▼
    ┌───────────────────┐ ┌──────────────────┐ ┌──────────────────┐
    │                   │ │                  │ │                  │
    │ Chart Calculation │ │  Interpretation  │ │  User Profile    │
    │ Service           │ │  Service         │ │  Service         │
    │                   │ │                  │ │                  │
    └─────────┬─────────┘ └────────┬─────────┘ └──────────────────┘
              │                    │
              │                    │
              ▼                    ▼
    ┌───────────────────┐ ┌──────────────────┐
    │                   │ │                  │
    │ Ephemeris Data    │ │ Notification     │
    │ Service           │ │ Service          │
    │                   │ │                  │
    └───────────────────┘ └──────────────────┘
```

## Service Definitions

### 1. API Gateway Service

**Responsibilities:**
- Route incoming requests to appropriate services
- Authentication and authorization
- API key validation and rate limiting
- Request/response transformation
- Service discovery integration
- Cross-cutting concerns (logging, tracing)

**Technologies:**
- API Gateway framework (Kong, Traefik, or custom FastAPI)
- JWT for authentication tokens
- Redis for rate limiting

### 2. Chart Calculation Service

**Responsibilities:**
- Planetary position calculations
- House system implementations
- Aspect calculations
- Transit calculations
- Chart data preparation

**Technologies:**
- FastAPI framework
- Flatlib astrological library
- Redis for caching calculation results
- PostgreSQL for storing calculation history

### 3. Interpretation Service

**Responsibilities:**
- Template-based interpretations
- AI-powered interpretations via OpenAI
- Multi-style interpretation support
- Interpretation caching and retrieval

**Technologies:**
- FastAPI
- Celery for async processing
- Redis for message broker and result backend
- OpenAI client for AI integrations

### 4. User Profile Service

**Responsibilities:**
- User profile management
- Saved chart storage
- User preferences
- Authentication (if implementing user accounts)

**Technologies:**
- FastAPI
- PostgreSQL for profile storage
- Redis for session caching

### 5. Ephemeris Data Service

**Responsibilities:**
- Provide ephemeris data for calculations
- Cache frequently accessed ephemeris data
- Optimize ephemeris data access patterns

**Technologies:**
- FastAPI
- Specialized database for time-series ephemeris data
- Redis for caching

### 6. Notification Service

**Responsibilities:**
- Email notifications
- Push notifications
- Scheduled report delivery

**Technologies:**
- FastAPI
- Message queue for notification requests
- SMTP/third-party email service integration

### 7. Web UI Service

**Responsibilities:**
- Serve web interface
- Client-side rendering
- User interface components
- Mobile-responsive design

**Technologies:**
- Flask or more modern framework
- Static file serving
- Progressive enhancement

### 8. Monitoring & Metrics Service

**Responsibilities:**
- Collect and aggregate logs
- Gather and expose metrics
- Health check coordination
- Alerting integration

**Technologies:**
- Prometheus for metrics collection
- Grafana for visualization
- Centralized logging system
- Health check API

## Communication Patterns

### Synchronous Communication (REST/GraphQL)

For direct service-to-service communication:
- API Gateway → Service communications
- User-initiated request flows

**Example Flow - Chart Generation:**
1. Client request → API Gateway
2. API Gateway → Chart Calculation Service
3. Chart Calculation Service returns data → API Gateway
4. API Gateway → Client response

### Asynchronous Communication (Event-Driven)

For long-running processes and loose coupling:
- Chart Calculation → Interpretation Service
- Any service → Notification Service
- System-wide events

**Example Flow - Async Interpretation:**
1. Interpretation request → Message Queue
2. Interpretation Service processes from queue
3. Completion event published
4. Notification Service subscribes to completion events

### Service Discovery

All services register with a service registry:
- Service startup: Register service endpoint
- Service discovery: Query registry for service location
- Health monitoring: Regular health check pings

## Data Management

### Database Per Service

Each service manages its own data:

- **Chart Calculation Service:**
  - Calculation history
  - Ephemeris cache
  
- **User Profile Service:**
  - User profiles
  - Saved charts
  - Authentication data

- **Interpretation Service:**
  - Interpretation templates
  - AI prompt configurations
  - Interpretation history

### Shared Data Considerations

- **Caching Strategy:**
  - Redis as distributed cache
  - Service-specific cache regions
  - TTL-based expiration policies

- **Data Consistency:**
  - Event sourcing pattern for data changes
  - CQRS for complex queries
  - Eventually consistent model

## Deployment Strategy

### Container Orchestration

- Docker containers for each service
- Kubernetes for orchestration
  - Deployment configurations
  - Service definitions
  - Ingress rules
  - Horizontal Pod Autoscalers

### Infrastructure as Code

- Terraform or similar for infrastructure provisioning
- Helm charts for Kubernetes deployments
- Environment-specific configurations

### Scaling Considerations

- Stateless services for horizontal scaling
- Resource-based autoscaling
- Independent scaling for computation-intensive services

## Migration Roadmap

### Phase 1: Foundation (1-2 months)

1. Set up API Gateway service
2. Implement service discovery mechanism
3. Extract Chart Calculation Service
4. Establish monitoring foundation

### Phase 2: Core Services (2-3 months)

1. Extract Interpretation Service
2. Extract User Profile Service
3. Implement data consistency patterns
4. Enhance API Gateway capabilities

### Phase 3: Supporting Services (1-2 months)

1. Implement Notification Service
2. Create Ephemeris Data Service
3. Migrate Web UI to modern stack
4. Expand monitoring capabilities

### Phase 4: Optimization (1-2 months)

1. Performance tuning
2. Security hardening
3. Documentation and developer experience
4. Advanced scaling capabilities

## Technology Stack

### Development

- **Languages:** Python, JavaScript/TypeScript
- **Frameworks:** FastAPI, Flask, React (optional for UI)
- **Tools:** Docker, Poetry/pip for dependency management

### Infrastructure

- **Containerization:** Docker
- **Orchestration:** Kubernetes or Docker Compose
- **Service Mesh:** Istio (optional for advanced networking)
- **API Gateway:** Kong, Traefik, or custom FastAPI

### Data Storage

- **Databases:** PostgreSQL, Redis
- **Message Broker:** Redis or RabbitMQ
- **Object Storage:** MinIO or S3-compatible storage

### Observability

- **Metrics:** Prometheus
- **Visualization:** Grafana
- **Logging:** ELK Stack or compatible stack
- **Tracing:** OpenTelemetry

## Observability & Monitoring

### Metrics Collection

Each service exposes:
- Request counts and latencies
- Error rates
- Resource utilization
- Business metrics

### Logging Strategy

- Structured JSON logging
- Correlation IDs for request tracing
- Centralized log aggregation
- Log level management

### Health Checks

- Liveness probes: Is the service running?
- Readiness probes: Is the service ready to accept requests?
- Dependency checks: Are all dependencies available?

## Security Considerations

### Authentication & Authorization

- JWT-based authentication
- Role-based access control
- API key management
- Rate limiting and throttling

### Data Protection

- TLS for all service communications
- Database encryption
- Secure credential management
- Data minimization principles

### API Security

- Input validation
- Output sanitization
- Protection against common attacks
- Regular security scanning

## Implementation Approach

We are following the **Strangler Fig Pattern** for a gradual migration:

1. **API Gateway Deployment** - Create a routing layer in front of the monolith
2. **Service Extraction** - Extract one bounded context at a time into microservices
3. **Gradual Transition** - Route traffic incrementally from monolith to microservices
4. **Monolith Retirement** - Remove the monolith once all functionality is migrated

## Migration Status

| Service | Status | Repository |
|---------|--------|------------|
| API Gateway | Planned | TBD |
| Chart Calculation | Planned | TBD |
| Interpretation | Planned | TBD |
| User Profile | Planned | TBD |
| Ephemeris Data | Planned | TBD |
| Task Management | Planned | TBD |
| Monitoring | Planned | TBD |
| Web UI | Planned | TBD |

---

This architecture document serves as a living guide for the migration process. It should be updated as implementation progresses and new insights are gained.