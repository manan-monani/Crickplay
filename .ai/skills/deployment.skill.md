# Deployment Skill

> Skill for deploying applications, managing environments, and CI/CD operations.

## Purpose

This skill enables AI agents to handle deployment tasks, container management, and environment configuration.

## Capabilities

### 1. Docker Operations

**Building Images:**
```bash
# Build with tag
docker build -t <image-name>:<tag> .

# Build with build args
docker build --build-arg ENV=production -t app:latest .
```

**Running Containers:**
```bash
# Run with port mapping
docker run -d -p 3000:3000 --name app app:latest

# Run with environment variables
docker run -d \
  -e DATABASE_URL=postgres://... \
  -e JWT_SECRET=... \
  -p 3000:3000 \
  app:latest

# Run with volume mount
docker run -d -v ./data:/app/data app:latest
```

**Docker Compose:**
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=app
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=${DB_PASSWORD}

  redis:
    image: redis:alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 2. Environment Configuration

**Environment Files:**
```
.env.example     # Template (committed)
.env.local       # Local development (not committed)
.env.staging     # Staging environment
.env.production  # Production environment
```

**Environment Variables:**
```bash
# Database
DATABASE_URL=postgres://user:pass@host:5432/db
DATABASE_POOL_SIZE=10

# Authentication
JWT_SECRET=your-secret-key
JWT_EXPIRES_IN=7d

# External Services
REDIS_URL=redis://localhost:6379
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Application
NODE_ENV=production
PORT=3000
LOG_LEVEL=info
```

### 3. CI/CD Pipeline

**GitHub Actions Workflow:**
```yaml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Run linting
        run: npm run lint

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t app:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push app:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          # Deployment commands here
```

### 4. Health Checks

**Health Endpoint:**
```javascript
app.get('/health', async (req, res) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    checks: {}
  };

  // Database check
  try {
    await db.query('SELECT 1');
    health.checks.database = 'healthy';
  } catch (error) {
    health.checks.database = 'unhealthy';
    health.status = 'unhealthy';
  }

  // Redis check
  try {
    await redis.ping();
    health.checks.redis = 'healthy';
  } catch (error) {
    health.checks.redis = 'unhealthy';
    health.status = 'unhealthy';
  }

  const statusCode = health.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(health);
});
```

### 5. Database Migrations

**Migration Commands:**
```bash
# Create migration
npm run migration:create -- --name add_users_table

# Run migrations
npm run migration:up

# Rollback
npm run migration:down

# Check status
npm run migration:status
```

**Migration File:**
```javascript
exports.up = async (knex) => {
  await knex.schema.createTable('users', (table) => {
    table.increments('id').primary();
    table.string('email').notNullable().unique();
    table.string('password').notNullable();
    table.string('name');
    table.timestamps(true, true);
  });
};

exports.down = async (knex) => {
  await knex.schema.dropTable('users');
};
```

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] Docker image built and tested
- [ ] Health endpoints working
- [ ] Monitoring configured

### Deployment

- [ ] Backup database (if needed)
- [ ] Run database migrations
- [ ] Deploy new version
- [ ] Verify health checks
- [ ] Monitor error rates
- [ ] Test critical paths

### Post-Deployment

- [ ] Monitor application metrics
- [ ] Check error logs
- [ ] Verify all features working
- [ ] Update deployment documentation
- [ ] Notify team if needed

## Rollback Procedure

```bash
# 1. Identify the issue
# Check logs, metrics, error reports

# 2. Rollback to previous version
docker pull app:previous-tag
docker-compose up -d app

# 3. Rollback database if needed
npm run migration:down

# 4. Verify rollback
curl http://localhost:3000/health

# 5. Document the issue
# Update .ai/memory/decisions.md with details
```

## Monitoring & Logging

**Log Format:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "info",
  "message": "Request processed",
  "context": {
    "requestId": "abc123",
    "userId": 456,
    "path": "/api/users",
    "method": "GET",
    "duration": 45
  }
}
```

**Key Metrics:**
- Request rate (requests/second)
- Error rate (errors/minute)
- Response time (p50, p95, p99)
- CPU/Memory usage
- Database connection pool
- Cache hit rate
