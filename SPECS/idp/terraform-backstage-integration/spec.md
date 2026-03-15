# Feature: Terraform + Backstage Integration Pattern

**Status**: Draft
**Tech Lead Review**: Not yet reviewed
**Branch**: sas-157-worker-deployments
**Working Directory**: `idp/`

## Summary
Define and implement the pattern for Backstage plugins to orchestrate Terraform operations (plan, apply, destroy) for infrastructure provisioning, with status feedback and error handling.

## Requirements

- Backstage plugins can trigger terraform apply/destroy operations
- Terraform operations run asynchronously with progress feedback
- Support plan-then-apply workflow (review before applying)
- Error handling with clear user feedback
- Terraform state management and locking
- Support multiple terraform modules (Temporal Cloud, K8s, etc.)
- Audit trail of who initiated what changes

## Acceptance Criteria

- [ ] Backstage plugin can initiate terraform apply
- [ ] User receives progress updates while terraform runs
- [ ] Failed terraform operations display errors clearly
- [ ] Plan review before apply works end-to-end
- [ ] Terraform state is secured and versioned
- [ ] Audit log shows who changed what

## Technical Approach

- Temporal workflow to orchestrate terraform operations
- Activities to run terraform CLI commands
- State storage: S3 backend with encryption, DynamoDB locking
- Feedback mechanism: signal handlers for progress updates
- Error handling: capture terraform output and display to user
- Plugin UI: wizard for plan review before apply

## Files Affected

- `idp/terraform/backend.tf` (state backend configuration)
- `idp/workflows/TerraformWorkflow.ts` (orchestration)
- `idp/workflows/activities/terraform-activities.ts` (CLI execution)
- `idp/plugins/terraform-plugin/` (Backstage plugin UI)

## Risks & Constraints

- Long-running operations: terraform apply can take 5-10 minutes
- State consistency: concurrent modifications must be prevented
- Error recovery: failed apply may leave partial state
- Credential management: terraform needs access to Temporal Cloud, K8s, etc.

## Notes

Depends on: temporal-cloud-provisioning, temporal-workflow-automation
Used by: backstage-control-plane (central integration point)
Related to: secrets-management (terraform credentials)
