# Feature: [Backstage Developer Portal]

**Status**: Draft | In Review | In Progress | Complete
**Tech Lead Review**: Not yet reviewed
**Branch**: [branch-name]

## Summary
This backstage portal simplifies Temporal Application resource bootstrapping including Compute, Temporal Resources, and other related concerns.

## Requirements

- Deploys Backstage into a Kubernetes cluster (local : Minikube)
- Deployes the single-binary version of Temporal into a Kubernetes cluster (local: Minikube)
- Creates a `TemporalProjectBackstagePlugin` that for a `{ProjectName}` that is itself a Temporal Workflow.
- A "Temporal Project" supports N environments, with a Temporal Namespace backing each environment using format `{projectname}-{environment}` 
- Will be extended later to support new Backstage plugins that will be:
  - Using Temporal Cloud Terraform provider for creating Temporal Namespaces (one per environment)
  - Using Temporal Cloud TF provider to create a ServiceAccount, APIKey
  - Using existing Kubernetes plugins to create k8s resources for Temporal Project (each environment in its own k8s namespace)
  - Creating k8s deployment manifests to deploy the Temporal Project Workers and APIs
- Installs the new plugin into Backstage 
- Exposes the Backstage UI to outside callers (via ingress controller)

## Acceptance Criteria

- [ ] Can access backstage UI hosted in the k8s cluster from browser
- [ ] A Temporal Cloud Namespace is created for `{ProjectName}`
- [ ] Can view in browser the `TemporalProjectBackstagePlugin` workflow from the Temporal UI hosted  in the k8s cluster

## Technical Approach

Brief description of the technical strategy:
- Components involved
  - Backstage (https://backstage.io/)
  - Terraform
  - Kubernetes
  - Temporal Cloud Terraform Provider
  - Temporal TypeScript SDK (for Backstage plugin dev)
  - Traefik ingress controller
- We should automate the installation of all the things related to this portal. So not just a README with comnand line details.
- Any new patterns or technologies?

## Files Affected

- `{root}/backstage-portal`

## Risks & Constraints

- This is the first spike of a entire portal for tenanted Temporal Application adoption.

## Notes

This project already details bring up minikube and other components in DEPLOYMENT.md.

