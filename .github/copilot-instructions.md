# Crickplay - Copilot Instructions

> Instructions for GitHub Copilot when working on this project.

## Project Context

This is the Crickplay project. When generating code:

1. Follow the conventions defined in `CLAUDE.md`
2. Use TypeScript with strict type checking
3. Follow the existing code structure and patterns
4. Write tests for new functionality

## Code Style

- Use ESLint and Prettier configuration
- Use meaningful variable and function names
- Add JSDoc comments for public APIs
- Prefer async/await over callbacks
- Use early returns to reduce nesting

## Git Commits

Follow conventional commit format:

- `feat(scope): description` - New features
- `fix(scope): description` - Bug fixes
- `docs(scope): description` - Documentation
- `refactor(scope): description` - Code refactoring

## Important Files

- `CLAUDE.md` - Main agent instructions
- `.ai/memory/tasks.md` - Current tasks
- `.ai/memory/decisions.md` - Architecture decisions
- `.ai/memory/architecture.md` - System architecture

## When Making Changes

1. Read relevant existing code first
2. Follow established patterns
3. Update documentation if behavior changes
4. Add tests for new functionality
5. Use proper error handling
