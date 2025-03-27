# Microservices Reorganization

This directory structure has been created to facilitate the migration from a monolithic architecture to a microservices-based architecture.

## Structure Overview

- `services/`: Contains individual microservices
- `shared/`: Contains shared code used by multiple services
- `infra/`: Contains infrastructure configuration
- `docs/`: Contains documentation
- `tests/`: Contains tests for each service

## Next Steps

1. Move code from the existing monolith into the appropriate service directories
2. Update imports to reflect the new structure
3. Test each service independently
4. Update Docker and Kubernetes configurations as needed

See MICROSERVICES_REORGANIZATION.md for the complete migration plan.
