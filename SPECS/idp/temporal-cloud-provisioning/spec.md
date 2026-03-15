# Feature: Temporal Cloud Provisioning via Terraform

**Status**: Draft
**Tech Lead Review**: Not yet reviewed
**Branch**: sas-157-worker-deployments
**Working Directory**: `idp/`

## Summary
Terraform-based provisioning of Temporal Cloud resources (namespaces, service accounts, API keys) to support dynamic environment creation from the backstage portal.

## Requirements

- Provision Temporal Cloud namespaces using Terraform
- Create service accounts and API keys for each environment
- Support naming convention: `{projectname}-{environment}`
- Manage mTLS certificates for secure Temporal Cloud connections
- Store provisioned credentials securely (via secrets-management)
- Support destruction/cleanup of resources
- Terraform state management across environments

## Acceptance Criteria

- [ ] Can provision Temporal Cloud namespace via terraform
- [ ] Service account and API key created automatically
- [ ] Credentials stored in secrets management system
- [ ] mTLS certificates generated and stored
- [ ] Terraform state secured and versioned
- [ ] Can destroy namespace and clean up resources

## Technical Approach

- HashiCorp Terraform with Temporal Cloud provider
- Terraform backend: S3 or similar for state storage
- Module structure for reusability across projects/environments
- Integration point: Backstage plugins trigger terraform apply/destroy
- Secrets output: credentials stored in Doppler/Sealed Secrets

## Files Affected

- `idp/terraform/` (new directory)
- `idp/terraform/modules/temporal-cloud-namespace/`
- `idp/terraform/modules/service-account/`
- `idp/terraform/environments/` (dev, staging, prod configs)

## Risks & Constraints

- Requires valid Temporal Cloud account and API credentials
- Terraform state contains sensitive information (must be encrypted)
- Namespace naming conflicts if not careful with conventions
- Cost implications of creating multiple Temporal Cloud namespaces

## Notes

Depends on: secrets-management (where to store TCloud API key for Terraform)
