-- PostgreSQL initialization script for Prior Authorization Agent
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Full-text search configuration dictionary
CREATE EXTENSION IF NOT EXISTS pg_trgm;
