# Setup Guide

> Complete setup instructions for development environment.

## Prerequisites

Before starting, ensure you have:

- [ ] Node.js 18+ installed (`node --version`)
- [ ] npm or yarn installed
- [ ] Git installed and configured
- [ ] Docker (optional, for containerized services)
- [ ] Access to required services (database, etc.)

## Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd Crickplay

# 2. Install dependencies
npm install

# 3. Set up environment
cp .env.example .env
# Edit .env with your values

# 4. Start development server
npm run dev
```

## Detailed Setup

### 1. Environment Configuration

Create `.env` file from example:

```bash
cp .env.example .env
```

Required variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `NODE_ENV` | Environment | development |
| `PORT` | Server port | 3000 |
| `DATABASE_URL` | Database connection | postgres://user:pass@localhost:5432/db |
| `JWT_SECRET` | JWT signing secret | your-secret-key |
| `REDIS_URL` | Redis connection | redis://localhost:6379 |

### 2. Database Setup

#### Option A: Local PostgreSQL

```bash
# Create database
createdb crickplay_dev

# Run migrations
npm run db:migrate

# Seed initial data (optional)
npm run db:seed
```

#### Option B: Docker

```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Run migrations
npm run db:migrate
```

### 3. Redis Setup (If Required)

```bash
# Local Redis
redis-server

# Or with Docker
docker-compose up -d redis
```

### 4. MCP Servers Setup

For AI agent capabilities, configure MCP servers:

1. Review `.vscode/mcp.json` configuration
2. Set required environment variables:
   - `BRAVE_API_KEY` - For web search
   - `GITHUB_TOKEN` - For GitHub operations
   - Add other required keys

### 5. Running the Application

```bash
# Development mode (with hot reload)
npm run dev

# Production build
npm run build
npm start

# With Docker
docker-compose up
```

## Development Tools

### Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm start` | Start production server |
| `npm test` | Run tests |
| `npm run lint` | Run linter |
| `npm run format` | Format code |
| `npm run db:migrate` | Run database migrations |
| `npm run db:seed` | Seed database |

### VS Code Extensions

Recommended extensions:

- ESLint
- Prettier
- GitLens
- Docker
- Database Client (for viewing data)

### Testing

```bash
# Run all tests
npm test

# Run specific test file
npm test -- path/to/test.ts

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port
lsof -i :3000

# Kill process
kill -9 <PID>
```

#### Database Connection Failed

- Verify DATABASE_URL is correct
- Check if database server is running
- Verify network access to database

#### Dependencies Issues

```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### Permission Denied

```bash
# Fix npm permissions
sudo chown -R $(whoami) ~/.npm
```

## Project Structure

```
Crickplay/
├── src/              # Source code
├── tests/            # Test files
├── docs/             # Documentation
├── .ai/              # AI agent configuration
├── .vscode/          # VS Code settings
├── .github/          # GitHub configuration
├── docker/           # Docker files
└── scripts/          # Utility scripts
```

## Getting Help

- Check `CLAUDE.md` for AI agent instructions
- Review `.ai/memory/` for past decisions
- Check `docs/` for feature documentation
- Ask the AI agent for help with specific issues
