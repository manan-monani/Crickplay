# Generate API Prompt

> Use this prompt to generate API endpoints following project conventions.

## Trigger

Use when: Creating a new API endpoint or set of related endpoints.

## Input Required

- **Resource Name:** Name of the resource (e.g., "User", "Product")
- **Operations:** Which CRUD operations needed (Create, Read, Update, Delete)
- **Fields:** Data fields and their types
- **Authentication:** Required auth level
- **Special Requirements:** Any additional requirements

## Prompt Template

```
Generate a RESTful API for the [RESOURCE] resource.

## Resource Details

Name: [Resource Name]
Operations: [C/R/U/D operations needed]
Authentication: [public/authenticated/admin]

## Fields

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| [field1] | [type] | [yes/no] | [rules] |
| [field2] | [type] | [yes/no] | [rules] |

## Special Requirements

- [Any special requirements]

## Expected Output

1. Route definitions
2. Controller with handlers
3. Service layer logic
4. Input validation schema
5. Response types
6. Error handling
7. Unit tests

Follow the project conventions in CLAUDE.md and .ai/skills/backend.skill.md
```

## Example Usage

```
Generate a RESTful API for the Match resource.

## Resource Details

Name: Match
Operations: Create, Read, Update, Delete, List
Authentication: authenticated (admin for create/update/delete)

## Fields

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| id | uuid | auto | - |
| team1Id | uuid | yes | must exist |
| team2Id | uuid | yes | must exist, != team1Id |
| scheduledAt | datetime | yes | must be future |
| venue | string | yes | max 200 chars |
| status | enum | yes | scheduled/live/completed/cancelled |

## Special Requirements

- Include pagination for list endpoint
- Filter by status and date range
- Include team details in response
- Real-time updates endpoint for live matches

## Expected Output

Generate following project conventions...
```

## Output Validation

After generation, verify:

- [ ] Routes follow REST conventions
- [ ] Proper HTTP methods used
- [ ] Input validation implemented
- [ ] Error responses follow project format
- [ ] Tests cover happy path and errors
- [ ] Documentation generated
