# Feature Specifications

This directory contains specifications for features in development using Spec Driven Development with Claude Code.

## Structure

Specs are organized by scope:

```
SPECS/
├── idp/                          # Internal Developer Portal specs
│   ├── feature-name/
│   │   ├── spec.md       # Feature specification (REQUIRED)
│   │   ├── design.md     # Technical design details (optional)
│   │   └── PROGRESS.md   # Implementation progress tracking
│   └── ...
│
└── (future: other scopes)        # Non-IDP project features
```

**Note**: The `idp/` subdirectory contains all Internal Developer Portal specifications. These specs will be ported to a separate repository when the IDP matures. Organize any new feature specs into appropriate scopes.

## Workflow

1. **Spec Phase**: Write `spec.md` defining requirements and acceptance criteria
2. **Tech Lead Review**: Share spec with Claude Code for validation and design feedback
3. **Plan Phase**: I enter plan mode to design implementation approach
4. **Implementation**: Execute implementation with progress tracking in `PROGRESS.md`
5. **Verification**: Confirm all acceptance criteria are met

## Working Directory Convention

Each spec can specify a **Working Directory** that indicates the root for all file paths listed in "Files Affected":

```yaml
**Working Directory**: `idp/`
```

When a spec has `Working Directory: idp/`:
- All paths in "Files Affected" are relative to `idp/`
- Paths to files outside `idp/` use relative references (e.g., `../DEPLOYMENT.md`)
- This makes specs easily portable when moving `idp/` to a separate repository

**Example**:
```
Files Affected:
- `k8s/backstage/` (relative to idp/)
- `../DEPLOYMENT.md` (relative to project root, outside idp/)
```

## Template

Use `TEMPLATE.md` as a starting point for new specs.
