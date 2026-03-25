# Crickplay - AI Agent Instructions

> This file contains the master instructions for AI agents working on this project. Read this file completely before starting any task.

## Project Overview

**Project Name:** Crickplay
**Type:** [Define your project type - Web App / Mobile App / API / etc.]
**Tech Stack:** [Define your tech stack]

---

## Agent Behavior Guidelines

### Before Starting Any Task

1. **Read Memory Files First**
   - Check `.ai/memory/tasks.md` for pending tasks and current status
   - Check `.ai/memory/decisions.md` for architectural decisions made
   - Check `.ai/memory/architecture.md` for system design context
   - Check `docs/features/` for implemented features documentation

2. **Understand Context**
   - Use Context7 MCP to understand library APIs and best practices
   - Use sequential-thinking MCP for complex problem decomposition
   - Check existing code patterns before implementing new features

3. **Plan Before Implementing**
   - Break down complex tasks into smaller subtasks
   - Consider if branching is needed for experimental features
   - Document your approach in `.ai/memory/decisions.md` for significant changes

---

## Version Control Protocol (MANDATORY)

### Commit Convention (Conventional Commits)

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, semicolons)
- `refactor`: Code refactoring without feature change
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system or dependencies
- `ci`: CI/CD changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(auth): add JWT token refresh mechanism
fix(api): resolve null pointer in user endpoint
docs(readme): update installation instructions
refactor(database): optimize query performance
```

### Branching Strategy

```
main (production-ready)
  └── develop (integration branch)
        ├── feature/<feature-name>    # New features
        ├── fix/<bug-description>     # Bug fixes
        ├── refactor/<what>           # Code refactoring
        ├── experiment/<idea>         # Experimental (may be discarded)
        └── hotfix/<critical-fix>     # Critical production fixes
```

### When to Create Branches

| Scenario | Action |
|----------|--------|
| New feature implementation | Create `feature/<name>` from `develop` |
| Bug fix (non-critical) | Create `fix/<name>` from `develop` |
| Critical production bug | Create `hotfix/<name>` from `main` |
| Experimental/risky changes | Create `experiment/<name>` from `develop` |
| Refactoring existing code | Create `refactor/<name>` from `develop` |

### Commit Frequency

- Commit after completing each logical unit of work
- Commit before switching context or tasks
- Commit before any risky operation
- Never leave work uncommitted at end of session

### Auto-Commit Triggers

Agent should commit when:
1. A feature/subtask is completed
2. Tests are passing after implementation
3. Before starting a different task
4. After significant refactoring
5. Before pushing to remote

---

## Task Management Protocol

### Task Lifecycle

```
BACKLOG → TODO → IN_PROGRESS → REVIEW → DONE
```

### Task File: `.ai/memory/tasks.md`

Always update this file when:
- Starting a new task (move to IN_PROGRESS)
- Completing a task (move to DONE with completion date)
- Discovering new required tasks (add to BACKLOG)
- Blocking issues found (add BLOCKED status with reason)

### Task Priority Levels

- **P0 (Critical):** Blocking issues, security vulnerabilities
- **P1 (High):** Core feature implementation
- **P2 (Medium):** Enhancements, optimizations
- **P3 (Low):** Nice-to-have, documentation

---

## Documentation Protocol

### When to Document

- After implementing any new feature
- After making architectural decisions
- After discovering important patterns or gotchas
- After resolving complex bugs

### Documentation Locations

| Type | Location |
|------|----------|
| Feature documentation | `docs/features/<feature-name>.md` |
| API documentation | `docs/api/<endpoint-group>.md` |
| Architecture decisions | `.ai/memory/decisions.md` |
| System architecture | `.ai/memory/architecture.md` |
| Setup instructions | `docs/setup.md` |
| Deployment guide | `docs/deployment.md` |

---

## MCP Tools Usage

### Available MCPs and When to Use

| MCP | Purpose | When to Use |
|-----|---------|-------------|
| `sequential-thinking` | Complex problem decomposition | Multi-step problems, architectural decisions |
| `memory` | Persistent knowledge storage | Storing important learnings across sessions |
| `brave-search` | Web search | Finding solutions, documentation, best practices |
| `context7` | Library knowledge | Understanding APIs, library usage patterns |
| `slack` | Team communication | Notifications, status updates |
| `filesystem` | File operations | Reading/writing files outside workspace |
| `docker` | Container management | Building, running, managing containers |
| `dvc` | Data version control | Managing ML models, large datasets |
| `github` | GitHub operations | PR management, issue tracking, code review |

---

## Code Quality Standards

### Before Committing

1. Ensure code compiles/runs without errors
2. Run relevant tests
3. Format code according to project standards
4. Remove debug statements and console.logs
5. Update documentation if behavior changed

### Code Review Checklist (Self-Review)

- [ ] Code follows project conventions
- [ ] No hardcoded values (use config/env)
- [ ] Error handling is proper
- [ ] Security considerations addressed
- [ ] Performance impact considered
- [ ] Tests written/updated

---

## Session Workflow

### At Session Start

```
1. git pull origin develop
2. Read .ai/memory/tasks.md
3. Check .ai/memory/decisions.md for context
4. Identify next priority task
5. Create branch if needed
6. Start implementation
```

### At Session End

```
1. Commit all changes with proper message
2. Update .ai/memory/tasks.md
3. Document any decisions in .ai/memory/decisions.md
4. Push to remote if work is stable
5. Update feature docs if applicable
```

---

## Important Commands

```bash
# Version Control
git checkout -b feature/<name>    # Create feature branch
git commit -m "type(scope): msg"  # Commit with convention
git push -u origin <branch>       # Push branch to remote
git merge develop                 # Sync with develop

# Testing
npm test                          # Run tests
npm run lint                      # Check code style

# Documentation
npm run docs:build                # Build documentation
```

---

## Emergency Procedures

### Reverting Changes

```bash
# Revert last commit (keep changes)
git reset --soft HEAD~1

# Revert to specific commit
git revert <commit-hash>

# Discard all local changes (DANGEROUS)
git reset --hard origin/develop
```

### Recovery from Bad State

1. Check git reflog for recovery points
2. Use git stash to save current work
3. Document what went wrong in decisions.md
4. Ask for user confirmation before destructive operations

---

## File Structure Reference

```
Crickplay/
├── CLAUDE.md                    # This file - master instructions
├── .ai/
│   ├── instructions.md          # Detailed workflow instructions
│   ├── agents/
│   │   ├── coding-agent.md      # Coding agent behavior
│   │   ├── planner-agent.md     # Planning agent behavior
│   │   └── vcs-agent.md         # Version control agent
│   ├── skills/
│   │   ├── git.skill.md         # Git operations skill
│   │   ├── backend.skill.md     # Backend development skill
│   │   ├── deployment.skill.md  # Deployment skill
│   │   └── documentation.skill.md # Documentation skill
│   ├── prompts/
│   │   ├── generate-api.prompt.md
│   │   └── debug.prompt.md
│   ├── hooks/
│   │   ├── pre-run.json
│   │   └── post-run.json
│   └── memory/
│       ├── tasks.md             # Task tracking (READ FIRST)
│       ├── decisions.md         # Architectural decisions
│       └── architecture.md      # System architecture
├── docs/
│   ├── features/                # Feature documentation
│   ├── api/                     # API documentation
│   ├── setup.md                 # Setup instructions
│   └── deployment.md            # Deployment guide
├── .vscode/
│   └── mcp.json                 # MCP server configuration
└── .github/
    ├── copilot-instructions.md
    ├── PULL_REQUEST_TEMPLATE.md
    └── workflows/
        └── ci.yml               # CI/CD workflow
```

---

## Remember

1. **Always read memory files before starting work**
2. **Commit frequently with proper messages**
3. **Document as you go, not at the end**
4. **Create branches for risky or experimental work**
5. **Update task status in real-time**
6. **Ask user for confirmation on destructive operations**
