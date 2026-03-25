# Crickplay

> [Project description]

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd Crickplay

# Install dependencies
npm install

# Setup environment
cp .env.example .env
# Edit .env with your values

# Start development server
npm run dev
```

## Documentation

- [Setup Guide](docs/setup.md) - Development environment setup
- [Deployment Guide](docs/deployment.md) - Deployment instructions
- [Agent Workflow Guide](docs/AGENT_WORKFLOW_GUIDE.md) - Using AI agents

## Project Structure

```
Crickplay/
├── src/              # Source code
├── tests/            # Test files
├── docs/             # Documentation
├── .ai/              # AI agent configuration
└── .github/          # GitHub configuration
```

## Development

### Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm test` | Run tests |
| `npm run lint` | Run linter |

### AI Agent Workflow

This project uses an AI agent workflow for productive development. See the [Agent Workflow Guide](docs/AGENT_WORKFLOW_GUIDE.md) for details.

Key files:
- `CLAUDE.md` - Main agent instructions
- `.ai/memory/tasks.md` - Task tracking
- `.ai/memory/decisions.md` - Architectural decisions

## Contributing

1. Create a feature branch from `develop`
2. Make changes following project conventions
3. Submit a pull request

See [CLAUDE.md](CLAUDE.md) for coding conventions and commit guidelines.

## License

[License type]
