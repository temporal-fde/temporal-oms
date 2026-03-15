# Feature: Temporal Project Domain Model

**Status**: Draft
**Tech Lead Review**: Not yet reviewed
**Branch**: sas-157-worker-deployments
**Working Directory**: `idp/`

## Summary
Define the "Temporal Project" abstraction that represents a customer's Temporal application, including its structure, environments, resources, and lifecycle.

## Requirements

- Define "Temporal Project" entity and its attributes
- Support multiple environments per project (dev, staging, prod, etc.)
- Map projects to code repositories and deployment artifacts
- Define relationship between projects and Temporal namespaces
- Specify how projects relate to workers, workflows, and activities
- Define project lifecycle: creation, environment management, deletion
- Support multi-tenancy (different customers/orgs have different projects)

## Acceptance Criteria

- [ ] Temporal Project domain model documented
- [ ] Environment/namespace naming convention formalized
- [ ] Project-to-code mapping clear (repo structure, deployment model)
- [ ] Relationship to Temporal Cloud resources documented
- [ ] Lifecycle workflows defined
- [ ] Multi-tenant isolation strategy documented

## Technical Approach

- Domain-Driven Design: Project as bounded context
- Document model: attributes, relationships, invariants
- Specify database schema/entity relationships
- Define API contracts for project operations
- Backstage integration: how projects appear in catalog

## Files Affected

- `idp/docs/domain-model.md` (new)
- `idp/db/schema.sql` (entity definitions)
- `idp/api/schemas/` (OpenAPI specs for project operations)

## Risks & Constraints

- Abstraction risk: "Project" may be too vague or tightly coupled to Backstage
- Multi-tenancy: adds complexity to all downstream systems
- Schema changes: updating project model requires migrations

## Notes

Architectural foundation - affects all other specs that deal with projects/environments.
Questions to answer:
- Is a "Project" a Git repo, a business entity, or both?
- How do projects relate to teams/organizations?
- Can projects span multiple Temporal Cloud accounts?
