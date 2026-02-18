-- PostgreSQL initialization script for STRATUM PROTOCOL
-- Creates all required databases and schemas

-- =============================================================================
-- CREATE DATABASES
-- =============================================================================

CREATE DATABASE stratum_main;
CREATE DATABASE stratum_ledger;
CREATE DATABASE stratum_timeseries;

-- =============================================================================
-- STRATUM_MAIN SCHEMA (Core application data)
-- =============================================================================

\c stratum_main;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Infrastructure Nodes
CREATE TABLE IF NOT EXISTS infrastructure_nodes (
    id SERIAL PRIMARY KEY,
    node_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    node_type VARCHAR(100) NOT NULL,
    location JSONB,
    capacity FLOAT,
    current_load FLOAT DEFAULT 0,
    health_status FLOAT DEFAULT 1.0,
    criticality_score FLOAT DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_node_type ON infrastructure_nodes(node_type);
CREATE INDEX idx_location ON infrastructure_nodes USING GIN (location);
CREATE INDEX idx_criticality ON infrastructure_nodes(criticality_score DESC);

-- Infrastructure Dependencies
CREATE TABLE IF NOT EXISTS infrastructure_dependencies (
    id SERIAL PRIMARY KEY,
    source_node_id VARCHAR(255) REFERENCES infrastructure_nodes(node_id),
    target_node_id VARCHAR(255) REFERENCES infrastructure_nodes(node_id),
    dependency_type VARCHAR(100),
    strength FLOAT DEFAULT 1.0,
    bidirectional BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_source_node ON infrastructure_dependencies(source_node_id);
CREATE INDEX idx_target_node ON infrastructure_dependencies(target_node_id);

-- Simulation Results
CREATE TABLE IF NOT EXISTS simulation_results (
    id SERIAL PRIMARY KEY,
    simulation_id UUID DEFAULT uuid_generate_v4(),
    simulation_type VARCHAR(100),
    parameters JSONB,
    results JSONB,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_simulation_type ON simulation_results(simulation_type);
CREATE INDEX idx_simulation_status ON simulation_results(status);

-- Policy Actions
CREATE TABLE IF NOT EXISTS policy_actions (
    id SERIAL PRIMARY KEY,
    action_id UUID DEFAULT uuid_generate_v4(),
    policy_type VARCHAR(100),
    parameters JSONB,
    cost FLOAT,
    implementation_time INTEGER,
    status VARCHAR(50) DEFAULT 'proposed',
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================================
-- STRATUM_LEDGER SCHEMA (Cryptographic audit trail)
-- =============================================================================

\c stratum_ledger;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS decision_ledger (
    id SERIAL PRIMARY KEY,
    decision_id VARCHAR(255) UNIQUE NOT NULL,
    decision_type VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL,
    outcomes JSONB NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    authority VARCHAR(255) NOT NULL,
    previous_hash VARCHAR(64) NOT NULL,
    current_hash VARCHAR(64) UNIQUE NOT NULL,
    signature VARCHAR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_decision_timestamp ON decision_ledger(timestamp DESC);
CREATE INDEX idx_decision_authority ON decision_ledger(authority);
CREATE INDEX idx_current_hash ON decision_ledger(current_hash);

-- =============================================================================
-- STRATUM_TIMESERIES SCHEMA (Time-series data with TimescaleDB)
-- =============================================================================

\c stratum_timeseries;

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Sensor Data
CREATE TABLE IF NOT EXISTS sensor_data (
    time TIMESTAMPTZ NOT NULL,
    node_id VARCHAR(255) NOT NULL,
    sensor_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(100),
    metric_value DOUBLE PRECISION,
    metadata JSONB
);

SELECT create_hypertable('sensor_data', 'time', if_not_exists => TRUE);

CREATE INDEX idx_sensor_node ON sensor_data (node_id, time DESC);
CREATE INDEX idx_sensor_metric ON sensor_data (metric_name, time DESC);

-- Events
CREATE TABLE IF NOT EXISTS urban_events (
    time TIMESTAMPTZ NOT NULL,
    event_id VARCHAR(255) UNIQUE,
    event_type VARCHAR(100),
    severity VARCHAR(50),
    location JSONB,
    affected_nodes TEXT[],
    description TEXT,
    metadata JSONB
);

SELECT create_hypertable('urban_events', 'time', if_not_exists => TRUE);

CREATE INDEX idx_event_type ON urban_events (event_type, time DESC);
CREATE INDEX idx_event_severity ON urban_events (severity, time DESC);

-- Continuous Aggregates (for performance)
CREATE MATERIALIZED VIEW IF NOT EXISTS sensor_data_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    node_id,
    metric_name,
    AVG(metric_value) as avg_value,
    MAX(metric_value) as max_value,
    MIN(metric_value) as min_value,
    COUNT(*) as count
FROM sensor_data
GROUP BY bucket, node_id, metric_name;

-- Retention policies (auto-delete old data)
SELECT add_retention_policy('sensor_data', INTERVAL '90 days');
SELECT add_retention_policy('urban_events', INTERVAL '180 days');

-- =============================================================================
-- GRANT PERMISSIONS
-- =============================================================================

\c stratum_main;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

\c stratum_ledger;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

\c stratum_timeseries;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
