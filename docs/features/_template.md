# Feature: [Feature Name]

> Template for documenting features. Copy this file and fill in details.

## Overview

Brief description of what this feature does and why it exists.

## User Story

```
As a [user type],
I want to [action],
So that [benefit].
```

## Status

| Attribute | Value |
|-----------|-------|
| Status | Draft / In Development / Complete |
| Version | 1.0 |
| Last Updated | YYYY-MM-DD |
| Related Tasks | TASK-XXX |

## Technical Implementation

### Architecture

How this feature fits into the overall system architecture.

### Components

| Component | Purpose | Location |
|-----------|---------|----------|
| Component 1 | Description | `path/to/file` |
| Component 2 | Description | `path/to/file` |

### Data Model

```sql
-- Database schema for this feature
CREATE TABLE feature_table (
  id SERIAL PRIMARY KEY,
  -- fields...
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Data Flow

```
User Action
    │
    ▼
Controller (validates input)
    │
    ▼
Service (business logic)
    │
    ▼
Repository (data access)
    │
    ▼
Database
    │
    ▼
Response ←←←←←←←
```

## API Endpoints

### GET /api/feature

**Description:** What this endpoint does

**Request:**
```http
GET /api/feature?param=value
Authorization: Bearer <token>
```

**Response (200):**
```json
{
  "success": true,
  "data": []
}
```

**Errors:**
- `401` - Unauthorized
- `404` - Not found

## Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `FEATURE_FLAG` | Enable/disable | No | true |

## Testing

### Unit Tests
- `tests/unit/feature.test.ts`

### Integration Tests
- `tests/integration/feature.test.ts`

### Manual Testing
1. Step 1
2. Step 2
3. Expected result

## Known Limitations

- Limitation 1
- Limitation 2

## Future Improvements

- [ ] Improvement 1
- [ ] Improvement 2

## Related Documentation

- [Architecture](../../.ai/memory/architecture.md)
- [API Documentation](../api/feature-api.md)
- [Decision Record](../../.ai/memory/decisions.md#related-decision)

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | YYYY-MM-DD | Initial implementation |
