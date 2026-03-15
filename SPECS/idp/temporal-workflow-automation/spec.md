# Feature: Temporal Workflow Automation for Portal Actions

**Status**: Draft
**Tech Lead Review**: Not yet reviewed
**Branch**: sas-157-worker-deployments
**Working Directory**: `idp/`

## Summary
Define and implement the TemporalProjectBackstagePlugin workflow that orchestrates Temporal resource provisioning, project setup, and management tasks triggered by Backstage portal actions.

## Requirements

- TemporalProjectBackstagePlugin workflow for creating new projects
- Orchestrate provisioning tasks: Temporal Cloud namespace, API keys, K8s resources
- Support environment creation within projects (dev, staging, prod)
- Workflow error handling and compensation (rollback on failure)
- Async notifications back to Backstage UI (workflow progress, completion)
- Workflow versioning for safe updates
- Support workflow triggers from Backstage plugins

## Acceptance Criteria

- [ ] TemporalProjectBackstagePlugin workflow defined and executable
- [ ] Can provision complete project (namespace + K8s resources) end-to-end
- [ ] Workflow handles errors with meaningful rollback
- [ ] Backstage UI receives progress updates from workflow
- [ ] Workflow version management prevents breaking running workflows
- [ ] Can manually trigger/debug workflow from Temporal UI

## Technical Approach

- TypeScript Temporal SDK for workflow definition
- Child workflows for modular provisioning steps
- Activities for external system interaction (Terraform, K8s APIs, Backstage)
- Workflow versioning with patching for safe updates
- Signal handlers for async communication back to Backstage
- Comprehensive error handling and compensation

## Files Affected

- `idp/workflows/` (new directory)
- `idp/workflows/TemporalProjectWorkflow.ts` (main workflow)
- `idp/workflows/activities/` (provisioning activities)
- `idp/workflows/tests/` (workflow tests)

## Risks & Constraints

- Workflow complexity: many sequential steps that can fail
- Long-running operations: Terraform apply can take minutes
- State consistency: ensuring idempotency across retries
- Versioning: managing workflow code updates safely

## Notes

Depends on: temporal-project-domain-model, temporal-cloud-provisioning
Triggers from: backstage-plugin-development (Backstage plugins call workflows)
