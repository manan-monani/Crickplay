# Backend Development Skill

> Skill for implementing backend features, APIs, and server-side logic.

## Purpose

This skill enables AI agents to implement backend functionality following best practices and project conventions.

## Capabilities

### 1. API Development

**RESTful Endpoints:**
```
GET    /api/resource          - List resources
GET    /api/resource/:id      - Get single resource
POST   /api/resource          - Create resource
PUT    /api/resource/:id      - Update resource
DELETE /api/resource/:id      - Delete resource
```

**Response Format:**
```json
{
  "success": true,
  "data": {},
  "message": "Operation successful",
  "meta": {
    "pagination": {}
  }
}
```

**Error Format:**
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {}
  }
}
```

### 2. Database Operations

**Query Best Practices:**
- Always use parameterized queries
- Index frequently queried columns
- Use transactions for multi-step operations
- Handle connection errors gracefully

**Example:**
```javascript
// Good - Parameterized
const user = await db.query(
  'SELECT * FROM users WHERE id = ?',
  [userId]
);

// Avoid - SQL Injection risk
const user = await db.query(
  `SELECT * FROM users WHERE id = ${userId}`
);
```

### 3. Authentication & Authorization

**JWT Token Structure:**
```javascript
{
  header: {
    alg: 'HS256',
    typ: 'JWT'
  },
  payload: {
    sub: userId,
    role: userRole,
    iat: issuedAt,
    exp: expiresAt
  }
}
```

**Middleware Pattern:**
```javascript
const authMiddleware = async (req, res, next) => {
  try {
    const token = extractToken(req);
    const decoded = verifyToken(token);
    req.user = decoded;
    next();
  } catch (error) {
    res.status(401).json({ error: 'Unauthorized' });
  }
};
```

### 4. Validation

**Input Validation:**
```javascript
const createUserSchema = {
  email: {
    type: 'string',
    format: 'email',
    required: true
  },
  password: {
    type: 'string',
    minLength: 8,
    required: true
  },
  name: {
    type: 'string',
    maxLength: 100,
    required: true
  }
};
```

### 5. Error Handling

**Error Classes:**
```javascript
class AppError extends Error {
  constructor(message, statusCode, code) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.isOperational = true;
  }
}

class NotFoundError extends AppError {
  constructor(resource) {
    super(`${resource} not found`, 404, 'NOT_FOUND');
  }
}

class ValidationError extends AppError {
  constructor(details) {
    super('Validation failed', 400, 'VALIDATION_ERROR');
    this.details = details;
  }
}
```

## Implementation Checklist

### Creating New Endpoint

- [ ] Define route with proper HTTP method
- [ ] Add authentication middleware if needed
- [ ] Validate input data
- [ ] Implement business logic
- [ ] Handle errors appropriately
- [ ] Return consistent response format
- [ ] Add tests
- [ ] Document endpoint

### Database Migration

- [ ] Create migration file
- [ ] Define up and down operations
- [ ] Test migration locally
- [ ] Document schema changes
- [ ] Update related models

### Adding New Service

- [ ] Create service class/module
- [ ] Implement dependency injection
- [ ] Add error handling
- [ ] Write unit tests
- [ ] Document public methods

## Code Patterns

### Service Layer

```javascript
class UserService {
  constructor(userRepository, emailService) {
    this.userRepository = userRepository;
    this.emailService = emailService;
  }

  async createUser(userData) {
    // Validation
    this.validateUserData(userData);

    // Business logic
    const hashedPassword = await hashPassword(userData.password);
    const user = await this.userRepository.create({
      ...userData,
      password: hashedPassword
    });

    // Side effects
    await this.emailService.sendWelcome(user.email);

    return user;
  }
}
```

### Repository Pattern

```javascript
class UserRepository {
  async findById(id) {
    return await db.query('SELECT * FROM users WHERE id = ?', [id]);
  }

  async create(userData) {
    const result = await db.query(
      'INSERT INTO users (email, password, name) VALUES (?, ?, ?)',
      [userData.email, userData.password, userData.name]
    );
    return { id: result.insertId, ...userData };
  }

  async update(id, userData) {
    await db.query(
      'UPDATE users SET name = ?, email = ? WHERE id = ?',
      [userData.name, userData.email, id]
    );
    return this.findById(id);
  }
}
```

## Testing Guidelines

### Unit Test Structure

```javascript
describe('UserService', () => {
  describe('createUser', () => {
    it('should create user with hashed password', async () => {
      // Arrange
      const userData = { email: 'test@test.com', password: 'pass123' };

      // Act
      const user = await userService.createUser(userData);

      // Assert
      expect(user.email).toBe(userData.email);
      expect(user.password).not.toBe(userData.password);
    });

    it('should throw on invalid email', async () => {
      // Arrange
      const userData = { email: 'invalid', password: 'pass123' };

      // Act & Assert
      await expect(userService.createUser(userData))
        .rejects.toThrow(ValidationError);
    });
  });
});
```

## Security Considerations

1. **Input Sanitization** - Always sanitize user input
2. **SQL Injection** - Use parameterized queries
3. **XSS** - Escape output in templates
4. **CSRF** - Use CSRF tokens for state-changing operations
5. **Rate Limiting** - Implement rate limits on sensitive endpoints
6. **Secrets** - Never hardcode secrets, use environment variables
