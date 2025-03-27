# CI/CD Pipeline for Natal Astrology Engine Microservices

This document outlines the continuous integration and continuous deployment (CI/CD) pipeline for the Natal Astrology Engine microservices architecture.

## Table of Contents

1. [Overview](#overview)
2. [Pipeline Architecture](#pipeline-architecture)
3. [Workflows](#workflows)
4. [Infrastructure as Code](#infrastructure-as-code)
5. [Pipeline Environments](#pipeline-environments)
6. [Automated Testing](#automated-testing)
7. [Deployment Strategy](#deployment-strategy)
8. [Security Practices](#security-practices)
9. [Monitoring & Feedback](#monitoring--feedback)
10. [Implementation Steps](#implementation-steps)

## Overview

Our CI/CD pipeline aims to automate the building, testing, and deployment of all microservices in the Natal Astrology Engine ecosystem, ensuring consistent quality, reliability, and rapid delivery of new features.

### Key Objectives

- **Automated Testing**: Run comprehensive test suites for all services
- **Continuous Integration**: Validate code changes against main branch
- **Continuous Delivery**: Automate the deployment process to multiple environments
- **Infrastructure as Code**: Manage infrastructure configuration through version control
- **Security Scans**: Integrate security scanning in the pipeline
- **Observability**: Monitor deployment success and application health

## Pipeline Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                           Developer Workflow                           │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│                           Source Code Management                       │
│                              (GitHub/GitLab)                           │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│                           CI/CD Pipeline Trigger                       │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
                  ┌─────────────────┼─────────────────┐
                  │                 │                 │
                  ▼                 ▼                 ▼
┌────────────────────────┐ ┌─────────────────┐ ┌───────────────────────┐
│                        │ │                 │ │                       │
│      Build Stage       │ │  Test Stage     │ │  Security Scan Stage  │
│                        │ │                 │ │                       │
└────────────┬───────────┘ └────────┬────────┘ └───────────┬───────────┘
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    │
                                    ▼
┌───────────────────────────────────────────────────────────────────────┐
│                             Artifact Storage                           │
└───────────────────────────────────┬───────────────────────────────────┘
                                    │
                        ┌───────────┴───────────┐
                        │                       │
                        ▼                       ▼
┌───────────────────────────────┐   ┌───────────────────────────────────┐
│                               │   │                                   │
│     Development Deployment    │   │     Staging Deployment            │
│                               │   │                                   │
└───────────────┬───────────────┘   └────────────────┬──────────────────┘
                │                                    │
                │                                    │
                │                                    ▼
                │                   ┌───────────────────────────────────┐
                │                   │                                   │
                ├──────────────────►│     Integration Testing           │
                │                   │                                   │
                │                   └────────────────┬──────────────────┘
                │                                    │
                │                                    │
                │                                    ▼
                │                   ┌───────────────────────────────────┐
                │                   │                                   │
                └──────────────────►│     Production Deployment         │
                                    │                                   │
                                    └────────────────┬──────────────────┘
                                                     │
                                                     ▼
                                    ┌───────────────────────────────────┐
                                    │                                   │
                                    │     Monitoring & Alerting         │
                                    │                                   │
                                    └───────────────────────────────────┘
```

## Workflows

### 1. Feature Branch Workflow

For development of new features:

1. Developer creates a feature branch from main
2. Developer commits changes and opens PR
3. CI pipeline runs:
   - Lint code
   - Run unit tests
   - Build Docker image
   - Run security scans
4. Manual code review
5. PR merged to main branch

### 2. Main Branch Workflow

When changes are merged to main:

1. CI pipeline runs:
   - Lint code
   - Run unit tests
   - Build Docker image
   - Run security scans
   - Tag image with commit hash
2. CD pipeline deploys to development environment
3. Run integration tests in development

### 3. Release Workflow

For creating releases:

1. Create release branch from main
2. CI pipeline runs full test suite
3. Tag Docker images with release version
4. Deploy to staging environment
5. Run integration and acceptance tests
6. Manual approval for production
7. Deploy to production
8. Post-deployment monitoring

## Infrastructure as Code

We'll use Terraform to manage our cloud infrastructure and Kubernetes resources:

### Terraform Structure

```
infrastructure/
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── staging/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── prod/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── modules/
│   ├── kubernetes/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── database/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── redis/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── backend.tf
```

### Kubernetes Manifests

For each microservice:

```
kubernetes/
├── base/
│   ├── api-gateway/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   ├── chart-calculation-service/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   └── ...
└── overlays/
    ├── dev/
    │   ├── api-gateway/
    │   │   ├── kustomization.yaml
    │   │   └── config-patch.yaml
    │   └── ...
    ├── staging/
    │   └── ...
    └── prod/
        └── ...
```

## Pipeline Environments

### Development Environment

- Purpose: Test new features and changes
- Deployment: Automatic on merge to main
- Data: Sanitized subset of production data
- Scale: Minimal resources
- Access: Development team only

### Staging Environment

- Purpose: Pre-production validation
- Deployment: Automatic on release creation, manual approval
- Data: Full production-like dataset
- Scale: Production-like resources
- Access: Development team and stakeholders

### Production Environment

- Purpose: Live service
- Deployment: Manual approval after staging validation
- Data: Production data
- Scale: Full production resources with autoscaling
- Access: Limited to DevOps team

## Automated Testing

### Unit Tests

- Run on every commit
- Focus on individual service components
- Mock external dependencies
- Coverage targets: >80%

### Integration Tests

- Run after deployment to development/staging
- Test service-to-service communication
- Use real dependencies (DB, Redis)
- API contract validation

### Load Tests

- Run on staging environment
- Simulate expected user load
- Measure response times and error rates
- Verify scaling behavior

### Security Tests

- Static Application Security Testing (SAST)
- Dynamic Application Security Testing (DAST)
- Dependency vulnerability scanning
- Secrets scanning

## Deployment Strategy

### Deployment Techniques

1. **Blue/Green Deployment**:
   - Deploy new version alongside existing version
   - Switch traffic when new version is validated
   - Quick rollback by switching traffic back

2. **Canary Deployments**:
   - Gradually increase traffic to new version
   - Monitor for errors and performance issues
   - Automatically rollback if issues detected

### Rollback Procedures

1. **Automated Rollbacks**:
   - Health checks fail → automatic rollback
   - Error rate threshold exceeded → automatic rollback
   - Performance degradation → automatic rollback

2. **Manual Rollbacks**:
   - Revert to previous known-good deployment
   - Apply any necessary data migrations
   - Post-mortem analysis to prevent recurrence

## Security Practices

### Secret Management

- Store secrets in a secure vault (HashiCorp Vault or cloud provider equivalent)
- Inject secrets at runtime, not build time
- Rotate secrets regularly

### Access Control

- Principle of least privilege
- Role-based access control (RBAC)
- Multi-factor authentication for production access

### Scanning and Auditing

- Regular vulnerability scanning
- Container image scanning before deployment
- Compliance auditing

## Monitoring & Feedback

### Deployment Metrics

- Deployment frequency
- Lead time for changes
- Change failure rate
- Mean time to recovery

### Application Metrics

- Error rates
- Response times
- Resource utilization
- Business metrics

### Feedback Loops

- Deployment notifications to team
- Automatic issue creation for failed deployments
- Regular review of deployment metrics

## Implementation Steps

### Phase 1: CI Pipeline Setup (2-3 weeks)

1. Set up source code repositories for microservices
2. Configure CI tool (GitHub Actions, GitLab CI, or Jenkins)
3. Implement build, test, and security scan stages
4. Set up artifact storage

### Phase 2: Development Environment (2-3 weeks)

1. Create Terraform code for infrastructure
2. Set up Kubernetes cluster
3. Configure development environment
4. Implement development deployment pipeline

### Phase 3: Staging & Production (3-4 weeks)

1. Set up staging environment
2. Implement integration testing
3. Configure production environment
4. Set up production deployment pipeline with approvals

### Phase 4: Advanced Features (2-3 weeks)

1. Implement blue/green deployment
2. Set up canary deployments
3. Configure advanced monitoring
4. Implement auto-rollbacks

## Implementation Example: GitHub Actions

A GitHub Actions workflow for the Chart Calculation Service:

```yaml
name: Chart Calculation Service CI/CD

on:
  push:
    branches: [main]
    paths:
      - 'services/chart-calculation/**'
      - '.github/workflows/chart-calculation.yml'
  pull_request:
    branches: [main]
    paths:
      - 'services/chart-calculation/**'
      - '.github/workflows/chart-calculation.yml'

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:6
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd services/chart-calculation
          pip install -r requirements-dev.txt
      
      - name: Run linting
        run: |
          cd services/chart-calculation
          flake8 .
          black --check .
      
      - name: Run unit tests
        run: |
          cd services/chart-calculation
          pytest -xvs tests/unit
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
      
      - name: Run integration tests
        run: |
          cd services/chart-calculation
          pytest -xvs tests/integration
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
  
  build:
    name: Build and Push
    needs: test
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v1
      
      - name: Login to Container Registry
        uses: docker/login-action@v1
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v3
        with:
          images: ghcr.io/${{ github.repository }}/chart-calculation
          tags: |
            type=sha,format=long
            type=ref,event=branch
      
      - name: Build and push
        uses: docker/build-push-action@v2
        with:
          context: ./services/chart-calculation
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
  
  deploy-dev:
    name: Deploy to Development
    needs: build
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Install kubectl
        uses: azure/setup-kubectl@v1
      
      - name: Set Kubernetes context
        uses: azure/k8s-set-context@v1
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_DEV }}
      
      - name: Deploy to development
        run: |
          # Get image tag from previous job
          IMAGE_TAG=$(echo ${{ github.sha }} | cut -c1-7)
          
          # Update Kubernetes manifests
          cd kubernetes/overlays/dev/chart-calculation
          kustomize edit set image ghcr.io/${{ github.repository }}/chart-calculation:${IMAGE_TAG}
          
          # Apply manifests
          kustomize build . | kubectl apply -f -
          
          # Wait for deployment to be ready
          kubectl rollout status deployment/chart-calculation -n natal-astrology
```

## Best Practices & Recommendations

1. **Keep It Visible**: Make CI/CD pipeline status highly visible to the team
2. **Fail Fast**: Catch issues early in the pipeline to reduce wasted resources
3. **Consistent Environments**: Keep development, staging, and production as similar as possible
4. **Automate Everything**: Aim to automate every step from code to production
5. **Monitor the Pipeline**: Track pipeline health and speed to identify bottlenecks
6. **Treat Infrastructure as Code**: Version control all infrastructure configurations
7. **Secure Your Pipeline**: Protect CI/CD systems and credentials with the same rigor as production

## Next Steps

After implementing the basic CI/CD pipeline:

1. Implement metrics collection for deployment frequency and lead time
2. Add more sophisticated release strategies (feature flags, A/B testing)
3. Implement automated rollback based on monitoring data
4. Explore ChatOps integration for easier pipeline interaction
5. Add performance testing to the pipeline