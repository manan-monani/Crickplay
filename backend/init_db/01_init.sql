-- Initialize Crickplay Database
-- This script runs automatically when PostgreSQL container starts

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Set search path
ALTER DATABASE crickplay_db SET search_path TO public, auth, analytics;

-- Create initial tables will be handled by Alembic migrations
COMMENT ON DATABASE crickplay_db IS 'Crickplay Cricket Analytics SaaS Database';
