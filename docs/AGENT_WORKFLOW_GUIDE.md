# AI Agent Workflow Usage Guide

> How to use this agent workflow structure for productive development.

## Overview

This project is configured with a comprehensive AI agent workflow system that enables:

1. **Autonomous version control** - Proper commits, branching, and history tracking
2. **Persistent task management** - Task tracking across sessions
3. **Documentation automation** - Feature and API documentation
4. **Multi-tool integration** - MCP servers for extended capabilities

---

## Quick Start

### Starting a New Session

1. **The agent will automatically:**
   - Read `CLAUDE.md` for instructions
   - Check `.ai/memory/tasks.md` for pending tasks
   - Review recent decisions in `.ai/memory/decisions.md`
   - Sync with the remote repository

2. **Tell the agent what you want to work on:**
   ```
   "I want to implement user authentication"
   "Fix the bug where login fails on mobile"
   "Add a new API endpoint for match results"
   ```

3. **The agent will:**
   - Break down the task
   - Create appropriate branches
   - Implement with proper commits
   - Update documentation
   - Track progress in tasks.md

---

## Directory Structure

```
Crickplay/
├── CLAUDE.md                    # 🔴 MAIN AGENT INSTRUCTIONS
│
├── .ai/
│   ├── instructions.md          # Extended workflow details
│   │
│   ├── agents/
│   │   ├── coding-agent.md      # Coding implementation agent
│   │   ├── planner-agent.md     # Task planning agent
│   │   └── vcs-agent.md         # Version control agent
│   │
│   ├── skills/
│   │   ├── git.skill.md         # Git operations
│   │   ├── backend.skill.md     # Backend development
│   │   ├── deployment.skill.md  # Deployment operations
│   │   └── documentation.skill.md # Documentation
│   │
│   ├── prompts/
│   │   ├── generate-api.prompt.md  # API generation prompt
│   │   └── debug.prompt.md         # Debugging prompt
│   │
│   ├── hooks/
│   │   ├── pre-run.json         # Pre-session hooks
│   │   └── post-run.json        # Post-session hooks
│   │
│   └── memory/                  # 🔴 PERSISTENT STATE
│       ├── tasks.md             # Task tracking
│       ├── decisions.md         # Architectural decisions
│       └── architecture.md      # System architecture
│
├── docs/
│   ├── features/                # Feature documentation
│   ├── api/                     # API documentation
│   ├── setup.md                 # Setup guide
│   └── deployment.md            # Deployment guide
│
├── .vscode/
│   └── mcp.json                 # MCP server configuration
│
└── .github/
    ├── copilot-instructions.md  # GitHub Copilot settings
    ├── PULL_REQUEST_TEMPLATE.md
    ├── ISSUE_TEMPLATE/
    └── workflows/
        └── ci.yml               # CI/CD pipeline
```

---

## Working with Tasks

### Viewing Current Tasks

Ask the agent:
```
"What tasks are pending?"
"Show me the current task status"
"What should I work on next?"
```

### Adding New Tasks

```
"Add a task to implement password reset"
"I need to add caching - create tasks for this"
```

### Updating Task Status

The agent automatically updates tasks, but you can also:
```
"Mark the login feature as complete"
"This task is blocked by database migration"
```

---

## Version Control

### Automatic Behavior

The agent will automatically:
- Create branches for new features/fixes
- Make commits with conventional format
- Keep track of changes for potential reverts

### Manual Requests

```
"Create a new branch for the payment feature"
"Commit the current changes"
"Push to remote"  # Agent will ask for confirmation
"Show me recent commits"
"Revert the last commit"  # Agent will confirm first
```

### Branch Naming

| Type | Example |
|------|---------|
| Feature | `feature/user-authentication` |
| Bug Fix | `fix/login-redirect-issue` |
| Refactor | `refactor/api-structure` |
| Experiment | `experiment/new-caching` |
| Hotfix | `hotfix/security-patch` |

---

## MCP Tools Usage

### Available Tools

The project is configured with these MCP servers:

| MCP | Purpose | Usage |
|-----|---------|-------|
| `sequential-thinking` | Complex problem decomposition | Automatic for complex tasks |
| `memory` | Persistent storage | Cross-session knowledge |
| `brave-search` | Web search | Finding solutions |
| `context7` | Library documentation | API knowledge |
| `mysql/postgres` | Database operations | Direct queries |
| `github` | Repository operations | PR/Issue management |
| `slack` | Notifications | Team updates |
| `docker` | Container management | Deployment |

### Setup Required

1. Copy `.env.example` to `.env`
2. Fill in required API keys:
   - `BRAVE_API_KEY` - Get from brave.com/search/api
   - `GITHUB_TOKEN` - GitHub personal access token
   - `SLACK_BOT_TOKEN` - From Slack app settings
   - Database credentials

---

## Documentation

### Automatic Documentation

After implementing features, ask:
```
"Document the user authentication feature"
"Generate API documentation for the match endpoints"
```

### Templates

Use templates in `docs/features/_template.md` and `docs/api/_template.md`.

---

## Best Practices

### Do's ✅

1. **Start each session with context:**
   ```
   "Continue working on the authentication feature"
   "What progress was made on the API?"
   ```

2. **Be specific about requirements:**
   ```
   "Add login with JWT tokens, store refresh tokens in Redis"
   ```

3. **Request branches for risky work:**
   ```
   "Create an experiment branch for trying the new cache strategy"
   ```

4. **Ask for documentation:**
   ```
   "Document this feature for future reference"
   ```

5. **Review before pushing:**
   ```
   "Show me what will be pushed to remote"
   ```

### Don'ts ❌

1. **Don't skip reading memory files** - Context is important
2. **Don't manually edit memory files** - Let the agent maintain them
3. **Don't push without review** - Agent will ask confirmation
4. **Don't skip commit messages** - They help with future reverts

---

## Troubleshooting

### Agent Not Following Instructions

Check that `CLAUDE.md` is in the root directory.

### Tasks Not Persisting

Verify `.ai/memory/tasks.md` exists and is writable.

### MCP Tools Not Working

1. Check `.vscode/mcp.json` configuration
2. Verify environment variables are set
3. Ensure npm packages are installed: `npx -y @modelcontextprotocol/server-<name>`

### Git Operations Failing

1. Ensure git is initialized: `git init`
2. Check remote is configured: `git remote -v`
3. Verify credentials are set up

---

## Commands Reference

### Task Management
```
"Show tasks"            - View current tasks
"Add task: [desc]"      - Add new task
"Complete task [id]"    - Mark task complete
"What's blocking?"      - Show blocked tasks
```

### Version Control
```
"Create branch [name]"  - Create new branch
"Commit changes"        - Commit with proper message
"Push to remote"        - Push (with confirmation)
"Show history"          - View recent commits
"Revert [commit]"       - Revert changes
```

### Documentation
```
"Document [feature]"    - Create feature docs
"Update API docs"       - Update API documentation
"Record decision"       - Add to decisions.md
```

### Development
```
"Implement [feature]"   - Start implementing
"Debug [issue]"         - Start debugging session
"Generate API for [x]"  - Generate API endpoints
"Run tests"             - Execute test suite
```

---

## Support

- Check `CLAUDE.md` for detailed instructions
- Review `.ai/` directory for specific agent behaviors
- See `docs/` for project documentation
- Ask the agent for help: `"How do I [task]?"`
