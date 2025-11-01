-- Initialization script for UW Scanner database
-- This runs automatically when PostgreSQL container starts

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create database if not exists (handled by POSTGRES_DB env var)
-- Additional setup can go here

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE uw_scanner TO uw_user;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;
GRANT ALL ON SCHEMA public TO uw_user;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'UW Scanner database initialized successfully';
    RAISE NOTICE 'TimescaleDB extension: enabled';
    RAISE NOTICE 'User: uw_user';
    RAISE NOTICE 'Database: uw_scanner';
END $$;
