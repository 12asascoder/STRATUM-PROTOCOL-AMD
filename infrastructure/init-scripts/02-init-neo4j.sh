#!/bin/bash
# Neo4j initialization script for Knowledge Graph

set -e

echo "Waiting for Neo4j to be ready..."
until cypher-shell -u neo4j -p stratumgraph123 "RETURN 1" > /dev/null 2>&1; do
    sleep 2
done

echo "Creating constraints and indexes..."

cypher-shell -u neo4j -p stratumgraph123 << 'CYPHER'

// Create constraints
CREATE CONSTRAINT node_id_unique IF NOT EXISTS
FOR (n:InfrastructureNode) REQUIRE n.node_id IS UNIQUE;

CREATE CONSTRAINT node_name IF NOT EXISTS
FOR (n:InfrastructureNode) REQUIRE n.name IS NOT NULL;

// Create indexes for performance
CREATE INDEX node_type_idx IF NOT EXISTS
FOR (n:InfrastructureNode) ON (n.node_type);

CREATE INDEX criticality_idx IF NOT EXISTS
FOR (n:InfrastructureNode) ON (n.criticality_score);

CREATE INDEX location_idx IF NOT EXISTS
FOR (n:InfrastructureNode) ON (n.location);

// Create sample data for testing
CREATE (n1:InfrastructureNode {
    node_id: 'POWER_GRID_001',
    name: 'Central Power Station',
    node_type: 'power_generation',
    capacity: 1000.0,
    current_load: 750.0,
    health_status: 1.0,
    criticality_score: 0.0,
    location: point({latitude: 40.7128, longitude: -74.0060})
});

CREATE (n2:InfrastructureNode {
    node_id: 'WATER_PUMP_001',
    name: 'Main Water Pump Station',
    node_type: 'water_supply',
    capacity: 500.0,
    current_load: 300.0,
    health_status: 0.95,
    criticality_score: 0.0,
    location: point({latitude: 40.7580, longitude: -73.9855})
});

CREATE (n3:InfrastructureNode {
    node_id: 'COMM_HUB_001',
    name: 'Communications Hub',
    node_type: 'communications',
    capacity: 100.0,
    current_load: 80.0,
    health_status: 1.0,
    criticality_score: 0.0,
    location: point({latitude: 40.7489, longitude: -73.9680})
});

// Create dependencies
MATCH (source:InfrastructureNode {node_id: 'WATER_PUMP_001'})
MATCH (target:InfrastructureNode {node_id: 'POWER_GRID_001'})
CREATE (source)-[:DEPENDS_ON {
    dependency_type: 'power_supply',
    strength: 1.0,
    bidirectional: false
}]->(target);

MATCH (source:InfrastructureNode {node_id: 'COMM_HUB_001'})
MATCH (target:InfrastructureNode {node_id: 'POWER_GRID_001'})
CREATE (source)-[:DEPENDS_ON {
    dependency_type: 'power_supply',
    strength: 0.8,
    bidirectional: false
}]->(target);

CYPHER

echo "Neo4j initialization complete!"
