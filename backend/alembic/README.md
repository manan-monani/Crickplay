# Alembic Migrations
This directory contains database migration scripts managed by Alembic.

## Usage

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# View migration history
alembic history

# View current revision
alembic current
```
