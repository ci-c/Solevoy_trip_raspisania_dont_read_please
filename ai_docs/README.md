# AI Documentation

This directory contains technical documentation and guidelines for AI-assisted development of the SZGMU Schedule Bot.

## Structure

```
ai_docs/
├── README.md                      # This file
├── from_user/                     # User-provided documents
│   ├── read_only/                 # Reference materials
│   └── *.txt                      # Academic regulations
├── legacy/                        # Archived documentation
│   ├── prompts/                   # Old agent prompts
│   ├── state/                     # Old agent state files
│   ├── system/                    # Old agent system
│   └── AGENT_*.md                 # Old agent documentation
├── API_REFERENCE.md               # Bot API documentation
├── ARCHITECTURE.md                # System architecture overview
├── CALLBACK_REFERENCE.md          # Telegram callback handlers
├── CODESTYLE.md                   # Code style guidelines
├── DEBUGGING.md                   # Debugging guide
├── DEVELOPMENT_GUIDE.md           # Development workflow
├── ERROR_HANDLING_GUIDE.md        # Error handling patterns
├── MODELS_REFERENCE.md            # Database models reference
├── TECHNICAL.md                   # Technical specifications
├── UX_REQUIREMENTS.md             # User experience requirements
├── VALIDATION_GUIDE.md            # Data validation guide
├── bot_architecture.md            # Bot architecture details
├── extended_bot_ux.md             # Extended UX specifications
├── modular_structure.md           # Module organization
├── szgmu_academic_analysis.md     # Academic domain analysis
└── szgmu_regulations_summary.md   # SZGMU regulations summary
```

## Documentation Categories

### Core Technical Documentation

These documents describe the current system architecture and implementation:

- **API_REFERENCE.md** - Complete API reference for bot endpoints and services
- **ARCHITECTURE.md** - High-level system architecture and design decisions
- **CALLBACK_REFERENCE.md** - Telegram callback handler patterns
- **MODELS_REFERENCE.md** - SQLAlchemy model definitions and relationships
- **bot_architecture.md** - Detailed bot implementation architecture
- **modular_structure.md** - Module organization and responsibilities

### Development Guidelines

Guidelines for consistent development practices:

- **CODESTYLE.md** - Python code style, formatting, and conventions
- **DEVELOPMENT_GUIDE.md** - Development workflow and best practices
- **DEBUGGING.md** - Debugging techniques and tools
- **ERROR_HANDLING_GUIDE.md** - Error handling patterns and strategies
- **VALIDATION_GUIDE.md** - Input validation and data sanitization
- **TECHNICAL.md** - Technical constraints and implementation notes

### User Experience

User-facing design and interaction patterns:

- **UX_REQUIREMENTS.md** - User experience requirements and principles
- **extended_bot_ux.md** - Detailed UX specifications and flows

### Domain Knowledge

SZGMU-specific domain information:

- **szgmu_academic_analysis.md** - Analysis of SZGMU academic structures
- **szgmu_regulations_summary.md** - Summary of SZGMU regulations
- **from_user/** - Official documents and regulations

### Legacy Documentation

Archived documentation from previous development approaches:

- **legacy/prompts/** - Old multi-agent system prompts
- **legacy/state/** - Old agent state management
- **legacy/system/** - Old agent orchestration system
- **legacy/AGENT_*.md** - Old agent coordination documentation

This documentation has been superseded by the SPECKIT workflow (see `.specify/README.md`).

## Usage Guidelines

### For AI Assistants

1. **Consult constitution first** - `.specify/memory/constitution.md` contains the authoritative principles
2. **Follow SPECKIT workflow** - Use `.codex/prompts/speckit.*.md` for feature development
3. **Reference technical docs** - Use these files for implementation details
4. **Ignore legacy docs** - Files in `legacy/` are historical and not current practice

### For Developers

1. **Update docs with code** - Keep documentation synchronized with implementation
2. **Refer to ARCHITECTURE.md** - For system design decisions
3. **Follow CODESTYLE.md** - For consistent code formatting
4. **Check DEVELOPMENT_GUIDE.md** - For workflow and process

## Relationship to SPECKIT

This documentation supports SPECKIT-driven development:

- **Constitution** (`.specify/memory/constitution.md`) - Overrides all other documentation
- **SPECKIT templates** (`.specify/templates/`) - Structure for new features
- **Technical docs** (this directory) - Implementation reference
- **Legacy docs** (this directory) - Historical context only

When conflicts arise, follow this precedence:
1. Constitution
2. Active specification in `specs/`
3. Technical documentation in `ai_docs/`
4. Code comments and inline documentation

## Maintenance

- **Add new docs** - Place in appropriate category
- **Update existing docs** - Keep synchronized with code changes
- **Deprecate old docs** - Move to `legacy/` with explanation
- **Review quarterly** - Ensure documentation remains accurate

## Related Resources

- **SPECKIT Documentation** - `.specify/README.md`
- **Constitution** - `.specify/memory/constitution.md`
- **Specifications** - `specs/*/spec.md`
- **Implementation Plans** - `specs/*/plan.md`
- **Repository Guidelines** - `AGENTS.md`
- **README** - `README.md`

---

**Last Updated**: 2025-11-18
**Documentation Version**: 2.0.0
