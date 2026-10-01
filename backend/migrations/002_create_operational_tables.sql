CREATE TABLE IF NOT EXISTS assessments (
    id VARCHAR PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    client VARCHAR(255),
    assessment_type VARCHAR(50) DEFAULT 'External',
    status VARCHAR(50) DEFAULT 'DRAFT',
    scope_text TEXT,
    exclusions TEXT,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_authorized BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS assessment_scopes (
    id VARCHAR PRIMARY KEY,
    assessment_id VARCHAR NOT NULL,
    target VARCHAR(512) NOT NULL,
    kind VARCHAR(50) DEFAULT 'cidr',
    allowed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS target_groups (
    id VARCHAR PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS targets (
    id VARCHAR PRIMARY KEY,
    canonical VARCHAR(2048) NOT NULL,
    original VARCHAR(2048) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    protocol VARCHAR(20),
    hostname VARCHAR(255),
    ip VARCHAR(100),
    port INTEGER,
    path VARCHAR(2048),
    environment VARCHAR(50),
    business_unit VARCHAR(255),
    criticality VARCHAR(50),
    owner VARCHAR(255),
    authorization_status VARCHAR(50) DEFAULT 'UNAUTHORIZED',
    scope_status VARCHAR(50) DEFAULT 'DRAFT',
    tags TEXT,
    notes TEXT,
    valid_from TIMESTAMP,
    valid_until TIMESTAMP,
    group_id VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_targets_canonical ON targets (canonical);

CREATE TABLE IF NOT EXISTS scope_exclusions (
    id VARCHAR PRIMARY KEY,
    original VARCHAR(2048) NOT NULL,
    canonical VARCHAR(2048) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS target_history (
    id VARCHAR PRIMARY KEY,
    target_id VARCHAR NOT NULL,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS findings (
    id VARCHAR PRIMARY KEY,
    finding_id VARCHAR(255) NOT NULL UNIQUE,
    assessment_id VARCHAR(255),
    title VARCHAR(1024) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    severity VARCHAR(50) DEFAULT 'MEDIUM',
    asset VARCHAR(255),
    ip VARCHAR(50),
    hostname VARCHAR(255),
    url VARCHAR(2048),
    port INTEGER,
    source_tool VARCHAR(255),
    validation_status VARCHAR(50) DEFAULT 'UNVERIFIED',
    confidence INTEGER DEFAULT 0,
    risk_score INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'OPEN',
    evidence TEXT,
    remediation TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
