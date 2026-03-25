# API Documentation: [Endpoint Group]

> Template for API documentation. Copy this file for each endpoint group.

Base URL: `/api/v1`

## Overview

Brief description of this API group.

## Authentication

| Requirement | Description |
|-------------|-------------|
| Type | Bearer Token (JWT) |
| Header | `Authorization: Bearer <token>` |
| Scope | Required scopes for this API |

---

## Endpoints

### Create [Resource]

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
  "name": "string (required, max 100)",
  "description": "string (optional, max 500)",
  "type": "string (enum: type1, type2)"
}
```

**Success Response (201):**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Resource Name",
    "description": "Description",
    "type": "type1",
    "createdAt": "2024-01-15T10:00:00Z",
    "updatedAt": "2024-01-15T10:00:00Z"
  }
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | VALIDATION_ERROR | Invalid request body |
| 401 | UNAUTHORIZED | Missing or invalid token |
| 403 | FORBIDDEN | Insufficient permissions |
| 409 | CONFLICT | Resource already exists |

---

### Get [Resource]

`GET /resource/:id`

Retrieves a single resource by ID.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Resource ID |

**Success Response (200):**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Resource Name",
    "description": "Description",
    "type": "type1",
    "createdAt": "2024-01-15T10:00:00Z",
    "updatedAt": "2024-01-15T10:00:00Z"
  }
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 401 | UNAUTHORIZED | Missing or invalid token |
| 404 | NOT_FOUND | Resource not found |

---

### List [Resources]

`GET /resource`

Returns paginated list of resources.

**Query Parameters:**

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| page | number | Page number (1-based) | 1 |
| limit | number | Items per page (1-100) | 20 |
| sort | string | Sort field | createdAt |
| order | string | Sort order (asc/desc) | desc |
| search | string | Search term | - |
| type | string | Filter by type | - |

**Success Response (200):**

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Resource 1"
    }
  ],
  "meta": {
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100,
      "pages": 5,
      "hasNext": true,
      "hasPrev": false
    }
  }
}
```

---

### Update [Resource]

`PUT /resource/:id`

Updates an existing resource.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Resource ID |

**Request Body:**

```json
{
  "name": "string (optional)",
  "description": "string (optional)"
}
```

**Success Response (200):**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Updated Name",
    "updatedAt": "2024-01-15T11:00:00Z"
  }
}
```

---

### Delete [Resource]

`DELETE /resource/:id`

Deletes a resource.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| id | uuid | Resource ID |

**Success Response (204):**

No content.

---

## Common Error Format

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {
      "field": "Additional details"
    }
  }
}
```

## Rate Limiting

| Limit | Value |
|-------|-------|
| Authenticated | 100 requests/minute |
| Unauthenticated | 20 requests/minute |

Headers:
- `X-RateLimit-Limit`: Maximum requests
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp
