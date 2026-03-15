# Feature: Backstage Plugin Development Environment

**Status**: Draft
**Tech Lead Review**: Not yet reviewed
**Branch**: sas-157-worker-deployments
**Working Directory**: `idp/`

## Summary
Set up development environment and tooling for building Backstage plugins, specifically for the TemporalProjectBackstagePlugin that manages Temporal resource provisioning.

## Requirements

- Node.js/TypeScript development environment configured
- Backstage plugin scaffolding and templates
- Plugin development and hot-reload support
- Testing framework for plugin code
- Integration with Temporal SDK for workflow triggering
- Plugin build and packaging pipeline
- Documentation for plugin developers

## Acceptance Criteria

- [ ] Can scaffold new Backstage plugin from template
- [ ] Plugin development server runs with hot reload
- [ ] Unit tests pass for plugin code
- [ ] Plugin can trigger Temporal workflows
- [ ] Built plugin can be installed in Backstage instance
- [ ] Developer documentation complete

## Technical Approach

- Node.js/npm workspaces for monorepo structure
- Backstage plugin scaffolding CLI
- Jest for testing
- Temporal TypeScript SDK for workflow integration
- Plugin packaging and versioning strategy
- CI/CD for plugin builds

## Files Affected

- `idp/plugins/` (new directory)
- `idp/plugins/temporal-project-plugin/` (main plugin)
- `idp/plugins/package.json` (monorepo root)
- `idp/package.json` (tooling)

## Risks & Constraints

- Backstage plugin ecosystem: rapid changes in Backstage APIs
- TypeScript/Node.js version management across plugins
- Plugin testing complexity: UI component testing

## Notes

Depends on: backstage-deployment (where plugins are deployed)
Related to: temporal-workflow-automation (for triggering workflows from plugin)
