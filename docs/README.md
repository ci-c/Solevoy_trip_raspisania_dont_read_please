# Future Feature Plans

This directory contains preliminary planning documents for future features.

## Contents

- **group_search_and_reports_plan.md** - Improved group search and reporting system
- **invitation_system_plan.md** - User invitation and referral system
- **payment_system_plan.md** - Payment integration for premium features

## Status

These documents represent **preliminary ideas** and are **not yet formal specifications**.

## Converting to SPECKIT

To implement any of these features, they must be converted to the SPECKIT format:

### Step 1: Create Specification
```bash
# Use the SPECKIT workflow to create a formal spec
# Example: /speckit.specify Implement group search improvements
```

This will create a new specification in `specs/[id]/spec.md` following the constitution-aligned template.

### Step 2: Generate Implementation Plan
```bash
# Create implementation plan from the spec
# Example: /speckit.plan
```

This creates `specs/[id]/plan.md` with architecture, phases, and risk assessment.

### Step 3: Break Down Tasks
```bash
# Generate actionable tasks
# Example: /speckit.tasks
```

This creates `specs/[id]/tasks.md` with prioritized, testable tasks.

### Step 4: Implement
```bash
# Execute implementation following TDD
# Example: /speckit.implement
```

## Important Notes

1. **Do NOT implement directly from these plans** - They lack:
   - Constitution compliance checks
   - Test-first requirements
   - Async service layer alignment
   - Success criteria

2. **Use as reference only** - These documents can inform the feature description when running `/speckit.specify`, but the formal specification will be generated through the SPECKIT workflow.

3. **Archive after conversion** - Once a feature has a formal spec in `specs/`, consider moving the preliminary plan to `docs/archive/` or removing it.

## SPECKIT Workflow

For proper feature development, always follow the SPECKIT workflow:

1. **Specify** → Create formal specification with user stories and test requirements
2. **Plan** → Generate implementation plan aligned with constitution
3. **Tasks** → Break down into independent, testable tasks
4. **Implement** → Execute with test-driven development
5. **Analyze** → Review for compliance and quality
6. **Checklist** → Verify quality gates

See `.specify/README.md` for complete SPECKIT documentation.

## Constitution Principles

All features must align with the five core principles:

1. **Canonical Schedule Data Discipline** - Single source of truth
2. **Async Telegram Orchestration** - Consistent async service layer
3. **Student Value First** - User-centric design
4. **Tests Before Code** - Mandatory TDD
5. **Operational Transparency & Resilience** - Observable operations

See `.specify/memory/constitution.md` for details.

---

**Last Updated**: 2025-11-18
**Documentation Status**: Preliminary planning only
