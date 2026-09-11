-- Simple SQL migration to create identity tables for MVP
-- Run this using psql or include in Alembic as a first migration

CREATE TABLE IF NOT EXISTS orgs (
    id VARCHAR PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR PRIMARY KEY,
    username VARCHAR(150) NOT NULL UNIQUE,
    email VARCHAR(255),
    password_hash TEXT NOT NULL,
    role_id INTEGER REFERENCES roles(id),
    org_id VARCHAR REFERENCES orgs(id),
    disabled BOOLEAN DEFAULT FALSE,
    token_version INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT now(),
    last_login TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR PRIMARY KEY,
    actor_id VARCHAR,
    action VARCHAR(255) NOT NULL,
    object_type VARCHAR(100),
    object_id VARCHAR(255),
    details TEXT,
    created_at TIMESTAMP DEFAULT now()
);
