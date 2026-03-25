# Deployment Guide

> Instructions for deploying the application to various environments.

## Environments

| Environment | Purpose | URL |
|-------------|---------|-----|
| Development | Local development | localhost:3000 |
| Staging | Pre-production testing | staging.example.com |
| Production | Live application | app.example.com |

## Quick Deploy

### Docker Deployment

```bash
# Build image
docker build -t crickplay:latest .

# Run container
docker run -d \
  --name crickplay \
  -p 3000:3000 \
  --env-file .env.production \
  crickplay:latest
```

### Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Scale
docker-compose up -d --scale app=3
```

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing (`npm test`)
- [ ] Code linted (`npm run lint`)
- [ ] Build successful (`npm run build`)
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] Backup current production state

### During Deployment

- [ ] Deploy new version
- [ ] Run database migrations
- [ ] Clear caches if needed
- [ ] Verify health endpoints
- [ ] Monitor error rates

### Post-Deployment

- [ ] Smoke test critical paths
- [ ] Monitor metrics for 15 minutes
- [ ] Update deployment documentation
- [ ] Notify team of deployment

## Database Migrations

### Running Migrations

```bash
# Check pending migrations
npm run db:migrate:status

# Run migrations
npm run db:migrate

# Rollback last migration (if needed)
npm run db:migrate:rollback
```

### Safe Migration Practices

1. **Always backup before migrations**
2. **Test migrations on staging first**
3. **Use transactions when possible**
4. **Have rollback plan ready**

## Rollback Procedure

### Quick Rollback

```bash
# Revert to previous Docker image
docker pull crickplay:previous
docker-compose down
docker tag crickplay:previous crickplay:latest
docker-compose up -d
```

### Database Rollback

```bash
# Rollback last migration
npm run db:migrate:rollback

# Rollback to specific version
npm run db:migrate:rollback --to <version>
```

### Full Rollback Steps

1. **Stop traffic** - Switch load balancer to maintenance
2. **Backup current** - Export any new data
3. **Restore previous** - Restore code and database
4. **Verify** - Test critical paths
5. **Resume traffic** - Switch load balancer back
6. **Document** - Record what happened

## Health Checks

### Application Health

```bash
# Check health endpoint
curl https://app.example.com/health

# Expected response
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:00:00Z",
  "checks": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### Infrastructure Health

```bash
# Check container status
docker ps

# Check container logs
docker logs crickplay

# Check resource usage
docker stats
```

## Monitoring

### Key Metrics to Watch

| Metric | Warning | Critical |
|--------|---------|----------|
| Response Time (p95) | > 500ms | > 1000ms |
| Error Rate | > 1% | > 5% |
| CPU Usage | > 70% | > 90% |
| Memory Usage | > 70% | > 90% |
| Database Connections | > 70% pool | > 90% pool |

### Monitoring Tools

- **Application:** Sentry, New Relic
- **Infrastructure:** Prometheus, Grafana
- **Logs:** ELK Stack, CloudWatch

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm test

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy
        run: |
          # Deployment commands
```

### Manual Deployment

When CI/CD is not available:

```bash
# 1. SSH to server
ssh deploy@server.example.com

# 2. Pull latest code
cd /app
git pull origin main

# 3. Install dependencies
npm ci --production

# 4. Build
npm run build

# 5. Run migrations
npm run db:migrate

# 6. Restart service
pm2 restart app
```

## Environment Variables

### Staging

```bash
NODE_ENV=staging
PORT=3000
DATABASE_URL=postgres://...
# Add staging-specific vars
```

### Production

```bash
NODE_ENV=production
PORT=3000
DATABASE_URL=postgres://...
# Add production-specific vars
```

### Secrets Management

- Use environment variables for secrets
- Never commit secrets to repository
- Use secret management services (AWS Secrets Manager, HashiCorp Vault)
- Rotate secrets regularly

## Scaling

### Horizontal Scaling

```bash
# Scale with Docker Compose
docker-compose up -d --scale app=3

# Scale with Kubernetes
kubectl scale deployment app --replicas=3
```

### Database Scaling

1. Add read replicas for read-heavy workloads
2. Implement connection pooling
3. Consider sharding for very large datasets

### Caching

1. Use Redis for session and frequent data
2. Implement CDN for static assets
3. Add browser caching headers

## Troubleshooting

### Application Won't Start

```bash
# Check logs
docker logs crickplay

# Check environment
docker exec crickplay env

# Check connectivity
docker exec crickplay curl http://localhost:3000/health
```

### Database Issues

```bash
# Check connection
docker exec crickplay npm run db:check

# Check migrations
docker exec crickplay npm run db:migrate:status
```

### High Memory Usage

```bash
# Check memory
docker stats crickplay

# Force garbage collection (if applicable)
# Restart container if needed
docker restart crickplay
```
