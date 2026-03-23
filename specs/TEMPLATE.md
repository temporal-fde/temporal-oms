# Feature Specification Template

Use this template for all feature specs. Copy to `SPECS/feature-name/spec.md` and fill in each section.

## Overview

**Feature Name:** [Feature Title]
**Status:** Draft / In Review / Approved / Implementing / Complete
**Owner:** [Your Name]
**Created:** [Date]
**Updated:** [Date]

### Executive Summary

[1-2 paragraph summary of what this feature is, why it matters, and what outcome we expect]

---

## Goals & Success Criteria

### Primary Goals
- Goal 1: [Measurable outcome]
- Goal 2: [Measurable outcome]
- Goal 3: [Measurable outcome]

### Acceptance Criteria
- [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2
- [ ] Acceptance criterion 3

---

## Current State (As-Is)

### What exists today?
[Describe the current system, patterns, and limitations]

### Pain points / gaps
- Gap 1: [Description]
- Gap 2: [Description]

---

## Desired State (To-Be)

### Architecture Overview
[High-level diagram or description of how the system works after this feature]

### Key Capabilities
- Capability 1: [What the system can do]
- Capability 2: [What the system can do]

---

## Technical Approach

### Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| Decision 1 | Why this choice | What else was considered |

### Component Design

#### Component 1
- **Purpose:** [What it does]
- **Responsibilities:** [What it owns]
- **Interfaces:** [What it exposes/consumes]

#### Component 2
- **Purpose:** [What it does]
- **Responsibilities:** [What it owns]
- **Interfaces:** [What it exposes/consumes]

### Data Model / Schemas
[Describe any new data structures, protos, database schemas]

### Configuration / Deployment
[Describe configuration files, environment variables, deployment topology]

---

## Implementation Strategy

### Phases

**Phase 1: [Name]**
- Deliverable 1
- Deliverable 2

**Phase 2: [Name]**
- Deliverable 1
- Deliverable 2

### Critical Files / Modules

To Create:
- `path/to/file.ext` - Purpose
- `path/to/file.ext` - Purpose

To Modify:
- `path/to/file.ext` - Changes needed
- `path/to/file.ext` - Changes needed

---

## Testing Strategy

### Unit Tests
- Test scenario 1: [What to verify]
- Test scenario 2: [What to verify]

### Integration Tests
- Test scenario 1: [What to verify]
- Test scenario 2: [What to verify]

### Load/Stress Testing
[If applicable, describe load generation and performance expectations]

### Validation Checklist
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Load test targets met
- [ ] Documentation complete

---

## Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|-----------|
| Risk 1 | High/Med/Low | High/Med/Low | How we prevent/handle |
| Risk 2 | High/Med/Low | High/Med/Low | How we prevent/handle |

---

## Dependencies

### External Dependencies
- Dependency 1: [Version/constraint]
- Dependency 2: [Version/constraint]

### Cross-Cutting Concerns
- Concern 1: [How this feature interacts with other systems]
- Concern 2: [How this feature interacts with other systems]

### Rollout Blockers
[Any prerequisites that must be complete before this can ship]

---

## Open Questions & Notes

### Questions for Tech Lead / Product
- [ ] Question 1?
- [ ] Question 2?

### Implementation Notes
[Any gotchas, assumptions, or important details for implementers]

---

## References & Links

- [Link 1: Description]
- [Link 2: Description]
