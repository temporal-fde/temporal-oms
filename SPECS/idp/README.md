# Internal Developer Portal (IDP) - Project Charter

**Status**: Foundational Design Phase
**Audience**: Product, Engineering, Customers
**Last Updated**: 2026-03-15

---

## Vision

The **Internal Developer Portal** is a self-service platform that enables developers and platform engineers to provision and manage Temporal-based applications across multiple environments with minimal operational overhead. It abstracts away infrastructure complexity while maintaining full control and auditability.

**One-sentence mission**: "From zero to production Temporal application in minutes, not days."

---

## Problem Statement

Today, deploying Temporal applications is hard:
- Manual steps: provisioning namespaces, setting up K8s, managing secrets
- No self-service: developers wait for ops to create environments
- Lack of consistency: different teams use different patterns
- High barrier to entry: requires deep knowledge of Temporal, Kubernetes, Terraform, cloud providers
- Limited visibility: hard to track what's running where and who owns it

The IDP solves this by providing **one unified interface** for:
- Creating new Temporal projects
- Managing environments (dev, staging, prod)
- Provisioning Temporal Cloud resources
- Deploying workers and APIs
- Viewing project status and workflows

---

## Goals

### For Developers
- ✅ Self-service project provisioning (no ops tickets)
- ✅ Consistent, best-practice infrastructure from day one
- ✅ Multi-environment support with clear naming conventions
- ✅ Clear visibility into what's deployed and how to manage it

### For Platform Engineers
- ✅ Portable solution that works anywhere (local, cloud, on-prem)
- ✅ Infrastructure-as-code approach (reproducible, version-controlled)
- ✅ Audit trail and access control
- ✅ Safe deployments with rollback support
- ✅ Ability to add new control planes later (Stripe dashboard, CLI, mobile, etc.)

### For Organizations
- ✅ Reduce time-to-value for Temporal adoption
- ✅ Lower operational burden (automate manual tasks)
- ✅ Enable multi-tenancy (support many customers/teams)
- ✅ Enterprise-grade security and compliance

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│           Backstage Developer Portal (UI)                │
│  (Accessible via browser: https://backstage.example.com) │
└─────────────────┬──────────────────────────────────────┘
                  │
        ┌─────────▼──────────┐
        │   Plugin System    │
        │  (TemporalProject  │
        │   BackstagePlugin) │
        └─────────┬──────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌─────────┐ ┌──────────┐ ┌────────────┐
│Temporal │ │Terraform │ │Kubernetes  │
│Workflows│ │Operations│ │Operations  │
└────┬────┘ └────┬─────┘ └────┬───────┘
     │            │             │
     └────────────┼─────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ▼             ▼             ▼
┌──────────────┐ ┌────────┐ ┌──────────┐
│Temporal Cloud│ │ Secrets│ │Kubernetes│
│  Namespaces  │ │Management │Clusters│
└──────────────┘ └────────┘ └──────────┘
```

---

## How It Works (User Journey)

### Step 1: Developer Creates Project via Backstage UI
```
Developer clicks "New Temporal Project" → Fills in:
  - Project Name: "my-commerce-app"
  - Team: "Commerce Team"
  - Environments: dev, staging, prod
```

### Step 2: Backstage Triggers Workflow
```
TemporalProjectBackstagePlugin Workflow starts:
  1. Create Temporal Project record in database
  2. For each environment:
     - Provision Temporal Cloud namespace: {projectname}-{environment}
     - Create service account and API key
     - Store credentials securely
  3. Create K8s namespaces for each environment
  4. Notify developer: "Project ready to deploy"
```

### Step 3: Developer Deploys Workers
```
Developer pushes code → GitHub Actions runs:
  1. Build Docker images
  2. Trigger Terraform to create K8s deployments
  3. Register workers with Temporal Cloud
  4. Backstage UI updates: "Workers deployed to dev"
```

### Step 4: Project Lifecycle Management
```
Developer can via Backstage UI:
  - View running workflows in each environment
  - Scale workers up/down
  - Create new environments
  - Rotate credentials
  - Delete projects (cleanup everything)
```

---

## Component Dependencies

```
FOUNDATION LAYER (Required before anything else):
  └─ Secrets Management
     └ Stores all credentials, API keys, certificates

INFRASTRUCTURE LAYER (Required for resource provisioning):
  ├─ Temporal Cloud Provisioning
  │  └ Creates Temporal Cloud namespaces via Terraform
  ├─ Kubernetes Ingress Setup
  │  └ Exposes Backstage and services via Traefik
  └─ Backstage Deployment
     └ Runs Backstage in Kubernetes

ARCHITECTURE LAYER (Required for domain model):
  └─ Temporal Project Domain Model
     └ Defines what a "Project" is, its structure, relationships

AUTOMATION LAYER (Required for orchestration):
  ├─ Temporal Workflow Automation
  │  └ TemporalProjectBackstagePlugin workflow for provisioning
  ├─ Terraform + Backstage Integration
  │  └ Pattern for invoking Terraform from plugins
  └─ Backstage Plugin Development
     └ Environment for building Backstage plugins

INTEGRATION LAYER (Pulls it all together):
  └─ Backstage Control Plane (backstage-portal)
     └ The complete IDP system using all above components
```

---

## Implementation Phases

### Phase 1: Foundations (Week 1-2)
- ✅ Secrets management (local + CI/CD + production)
- ✅ Temporal Cloud provisioning (Terraform setup)
- ✅ Backstage deployment to K8s

**Milestone**: "Can manually provision a Temporal Cloud namespace and deploy Backstage"

### Phase 2: Automation (Week 3-4)
- ✅ Temporal Project domain model
- ✅ Temporal workflow for provisioning
- ✅ Backstage plugin development environment

**Milestone**: "Can trigger namespace creation from a Backstage action"

### Phase 3: Integration (Week 5-6)
- ✅ Terraform + Backstage integration
- ✅ Kubernetes ingress setup
- ✅ End-to-end testing

**Milestone**: "Developer can provision complete project from Backstage UI"

### Phase 4: Polish & Docs (Week 7-8)
- ✅ Error handling and rollback
- ✅ Comprehensive documentation
- ✅ Team training

**Milestone**: "Ready for internal use"

---

## Success Criteria

### Technical
- [ ] All specs reviewed and approved
- [ ] All components deployed and working in Minikube
- [ ] End-to-end project creation workflow functional
- [ ] All tests passing
- [ ] Comprehensive documentation

### User-Facing
- [ ] Developer can create project in < 5 minutes
- [ ] Clear error messages and troubleshooting docs
- [ ] Backstage UI is intuitive (no prior Temporal knowledge required)
- [ ] Team adopts it for new projects (≥80% usage)

### Operational
- [ ] Full audit trail of who created what
- [ ] Secrets properly encrypted at rest and in transit
- [ ] Can recover from partial failures (rollback support)
- [ ] Monitoring and alerts for failures

---

## Scope: What's IN

- ✅ Backstage as primary control plane (first implementation)
- ✅ Temporal Cloud provisioning
- ✅ Multi-environment support (dev/staging/prod)
- ✅ Kubernetes deployment orchestration
- ✅ Secret management across environments
- ✅ Workflow automation for provisioning
- ✅ Documentation and runbooks

## Scope: What's OUT (for later)

- ❌ Other control planes (CLI, REST API, mobile) - designed for extensibility, build later
- ❌ Advanced features: dynamic scaling, cost optimization, multi-cloud orchestration
- ❌ Admin UI for team/organization management (use API/CLI for now)
- ❌ Marketplace for pre-built workflows
- ❌ Multi-region/multi-cloud deployments

---

## Design Principles

1. **Portability**: Works everywhere (local K8s, AWS, Azure, GCP, on-prem)
2. **Extensibility**: Built for multiple control planes from day one
3. **Safety**: Never break running workflows, support rollbacks
4. **Simplicity**: Hide complexity behind simple UI/API
5. **Observability**: Full audit trail and visibility
6. **Self-Service**: Developers control their own infrastructure
7. **Infrastructure-as-Code**: Everything version-controlled, reproducible

---

## Related Documentation

- **Spec Index**: See individual specs in this directory for details
- **DEPLOYMENT.md**: How to deploy this entire system
- **Architecture decisions**: See individual spec "Technical Approach" sections
- **Temporal Docs**: https://docs.temporal.io/
- **Backstage Docs**: https://backstage.io/docs/

---

## Getting Started

1. **Start here**: Read the specs in order (see Dependencies above)
2. **Deep dive**: Each spec has detailed Requirements and Technical Approach
3. **Implementation**: Use the spec-driven development process:
   - Read spec
   - Ask questions / request clarification
   - Get tech lead review
   - Enter plan mode for complex specs
   - Execute implementation
4. **Integration**: Follow Phase 1-4 timeline above

---

## Questions to Resolve (Before Starting Implementation)

These should be answered as you review the specs:

- What exactly is a "Temporal Project"? (see temporal-project-domain-model spec)
- How do we handle multi-tenancy? (customer isolation, billing, etc.)
- What's the disaster recovery strategy?
- How do we support teams/RBAC? (Backstage has plugins for this)
- What's the upgrade path when Temporal Cloud API changes?
- How do we handle failed provisioning? (rollback, cleanup)
- Should projects auto-scale? (out of scope for v1)

---

## Contact & Feedback

- **Owner**: [Your name/team]
- **Questions about IDP**: Review the relevant spec
- **Design feedback**: Create an issue or discussion
- **Implementation blockers**: Escalate to tech lead

---

## Related IDP Specs

**Foundation**: [secrets-management](./secrets-management/spec.md)
**Infrastructure**: [temporal-cloud-provisioning](./temporal-cloud-provisioning/spec.md) | [backstage-deployment](./backstage-deployment/spec.md) | [kubernetes-ingress-setup](./kubernetes-ingress-setup/spec.md)
**Architecture**: [temporal-project-domain-model](./temporal-project-domain-model/spec.md)
**Automation**: [temporal-workflow-automation](./temporal-workflow-automation/spec.md) | [terraform-backstage-integration](./terraform-backstage-integration/spec.md) | [backstage-plugin-development](./backstage-plugin-development/spec.md)
**Integration**: [backstage-control-plane](./backstage-portal/spec.md)
