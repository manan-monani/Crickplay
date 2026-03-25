# Documentation Skill

> Skill for creating and maintaining project documentation.

## Purpose

This skill enables AI agents to create comprehensive documentation that helps maintain project knowledge and onboarding.

## Documentation Types

### 1. Feature Documentation

**Location:** `docs/features/<feature-name>.md`

**Template:**
```markdown
# Feature: [Feature Name]

## Overview

Brief description of what this feature does and why it exists.

## User Story

As a [user type],
I want to [action],
So that [benefit].

## Technical Implementation

### Architecture

Describe the high-level architecture and how this feature fits into the system.

### Components

| Component | Purpose | Location |
|-----------|---------|----------|
| Component 1 | Description | `path/to/file` |
| Component 2 | Description | `path/to/file` |

### Data Flow

```
User Action → Controller → Service → Repository → Database
                                    ↓
                              Response ←
```

### Database Schema

```sql
CREATE TABLE feature_table (
  id INT PRIMARY KEY,
  field1 VARCHAR(255),
  field2 INT REFERENCES other_table(id),
  created_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### GET /api/feature

**Description:** Retrieves feature data

**Request:**
```
GET /api/feature?param=value
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": []
}
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| FEATURE_ENABLED | Toggle feature | true |
| FEATURE_LIMIT | Max items | 100 |

## Testing

### Unit Tests
- `test/feature/service.test.ts`
- `test/feature/controller.test.ts`

### Integration Tests
- `test/integration/feature.test.ts`

## Related

- [Related Feature 1](./related-feature-1.md)
- [Design Decision](../.ai/memory/decisions.md#feature-decision)
```

### 2. API Documentation

**Location:** `docs/api/<endpoint-group>.md`

**Template:**
```markdown
# API: [Endpoint Group]

Base URL: `/api/v1`

## Authentication

All endpoints require Bearer token authentication unless marked as public.

## Endpoints

### Create Resource

`POST /resource`

Creates a new resource.

**Headers:**
| Header | Value | Required |
|--------|-------|----------|
| Authorization | Bearer {token} | Yes |
| Content-Type | application/json | Yes |

**Request Body:**
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "type": "enum: ['type1', 'type2']"
}
```

**Success Response (201):**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Resource Name",
    "createdAt": "2024-01-15T10:00:00Z"
  }
}
```

**Error Responses:**

| Code | Description |
|------|-------------|
| 400 | Invalid request body |
| 401 | Unauthorized |
| 409 | Resource already exists |

### List Resources

`GET /resource`

Returns paginated list of resources.

**Query Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| page | number | Page number | 1 |
| limit | number | Items per page | 20 |
| sort | string | Sort field | createdAt |
| order | string | Sort order (asc/desc) | desc |

**Success Response (200):**
```json
{
  "success": true,
  "data": [],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5
  }
}
```
```

### 3. Architecture Documentation

**Location:** `.ai/memory/architecture.md`

**Structure:**
```markdown
# System Architecture

## Overview

High-level description of the system architecture.

## System Components

```
┌─────────────────────────────────────────────────────────┐
│                      Client Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Web App   │  │ Mobile App  │  │   Admin     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                      API Gateway                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │    Auth     │  │ Rate Limit  │  │   Routing   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  User    │  │  Game    │  │  Match   │             │
│  │ Service  │  │ Service  │  │ Service  │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     Data Layer                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ PostgreSQL│  │  Redis   │  │    S3    │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Request Flow
1. Client sends request
2. API Gateway validates auth
3. Request routed to service
4. Service processes business logic
5. Data layer accessed
6. Response returned

### Event Flow
For async operations, describe event/message flow.

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React/Next.js | Web UI |
| Backend | Node.js/Express | API Server |
| Database | PostgreSQL | Primary data store |
| Cache | Redis | Session, caching |
| Queue | Bull/Redis | Background jobs |
| Storage | S3 | File storage |

## Security Architecture

Describe authentication, authorization, encryption.

## Scalability Considerations

Document scaling strategies and bottlenecks.
```

## Documentation Checklist

### When Creating New Feature

- [ ] Create feature documentation in `docs/features/`
- [ ] Update API documentation if new endpoints
- [ ] Update architecture if new components
- [ ] Add to table of contents in main README

### When Modifying Feature

- [ ] Update feature documentation
- [ ] Update API examples if changed
- [ ] Update any affected diagrams
- [ ] Review and update related docs

### Documentation Quality

- [ ] Clear and concise language
- [ ] Code examples are correct and tested
- [ ] All links working
- [ ] Diagrams up to date
- [ ] No outdated information

## Style Guide

1. **Use active voice** - "The service processes requests" not "Requests are processed"
2. **Be concise** - Avoid unnecessary words
3. **Include examples** - Show, don't just tell
4. **Keep updated** - Documentation should match code
5. **Link related docs** - Help readers navigate
