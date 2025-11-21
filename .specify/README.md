# SPECKIT Documentation

This directory contains the SPECKIT (Specification Kit) infrastructure for structured feature development.

## Structure

```
.specify/
├── README.md              # This file
├── memory/                # Project memory and constitution
│   └── constitution.md    # Project principles and guidelines
├── scripts/               # Automation scripts
│   └── bash/              # Bash scripts for feature management
│       ├── common.sh                  # Shared functions
│       ├── check-prerequisites.sh     # Environment validation
│       ├── create-new-feature.sh      # Feature scaffolding
│       ├── setup-plan.sh              # Plan initialization
│       └── update-agent-context.sh    # Context management
└── templates/             # Document templates
    ├── spec-template.md         # Feature specification template
    ├── plan-template.md         # Implementation plan template
    ├── tasks-template.md        # Task breakdown template
    ├── checklist-template.md    # Quality checklist template
    └── agent-file-template.md   # Agent file template
```

## SPECKIT Workflow

SPECKIT provides a structured approach to feature development with the following steps:

### 1. Specification (`/speckit.specify`)
Creates a new feature specification in `specs/[id]/spec.md` with:
- User scenarios and testing requirements
- Functional requirements aligned with constitution
- Success criteria
- Edge cases

**Template**: `templates/spec-template.md`

### 2. Planning (`/speckit.plan`)
Generates an implementation plan in `specs/[id]/plan.md` with:
- Architecture decisions
- Phase breakdown
- Risk assessment
- Constitution compliance check

**Template**: `templates/plan-template.md`

### 3. Task Generation (`/speckit.tasks`)
Creates actionable tasks in `specs/[id]/tasks.md` with:
- Prioritized task list
- Dependencies
- Testing requirements
- Acceptance criteria

**Template**: `templates/tasks-template.md`

### 4. Implementation (`/speckit.implement`)
Executes the implementation following test-driven development:
- Write failing tests first (Principle IV)
- Implement features
- Maintain async patterns (Principle II)
- Preserve canonical data flow (Principle I)

### 5. Analysis (`/speckit.analyze`)
Reviews implementation for:
- Constitution compliance
- Test coverage
- Code quality
- Documentation completeness

### 6. Checklist (`/speckit.checklist`)
Quality gate verification using `templates/checklist-template.md`

## Constitution

The project constitution (`memory/constitution.md`) defines five core principles:

1. **Canonical Schedule Data Discipline** - Single source of truth for schedule data
2. **Async Telegram Orchestration** - Consistent async service layer
3. **Student Value First** - User-centric design and error handling
4. **Tests Before Code** - Mandatory test-driven development
5. **Operational Transparency & Resilience** - Observable, resilient operations

All feature work MUST align with these principles.

## Commands

SPECKIT commands are available via `.codex/prompts/`:

- `/speckit.specify [description]` - Create feature specification
- `/speckit.plan` - Generate implementation plan
- `/speckit.tasks` - Break down into tasks
- `/speckit.implement` - Execute implementation
- `/speckit.analyze` - Review implementation
- `/speckit.checklist` - Run quality gates
- `/speckit.clarify` - Resolve ambiguities
- `/speckit.constitution` - Review/update constitution

## Scripts Usage

### Create New Feature
```bash
.specify/scripts/bash/create-new-feature.sh --json "feature description"
```

Returns JSON with `BRANCH_NAME` and `SPEC_FILE` paths.

### Setup Plan
```bash
.specify/scripts/bash/setup-plan.sh [spec-id]
```

Initializes plan.md for a specification.

### Check Prerequisites
```bash
.specify/scripts/bash/check-prerequisites.sh
```

Validates environment and dependencies.

## Best Practices

1. **Always start with specification** - No code without approved spec
2. **Follow test-first approach** - Write failing tests before implementation
3. **Document constitution alignment** - Every plan includes constitution check
4. **Keep stories independent** - Each user story should be deployable
5. **Track complexity** - Document deviations and technical debt

## Version

SPECKIT Version: 1.0.0
Constitution Version: 1.0.0
Last Updated: 2025-11-18
