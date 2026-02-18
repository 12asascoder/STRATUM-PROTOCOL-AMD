# STRATUM PROTOCOL - API Reference

## Base URLs

| Environment | Base URL |
|-------------|----------|
| Development | `http://localhost:8000` |
| Staging | `https://staging-api.stratum-protocol.io` |
| Production | `https://api.stratum-protocol.io` |

## Authentication

All API requests require authentication via JWT Bearer tokens.

```http
Authorization: Bearer <your_jwt_token>
```

### Obtaining a Token

```bash
curl -X POST https://api.stratum-protocol.io/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

---

## Data Ingestion API

**Base Path**: `/api/v1/ingest`

### Ingest Single Data Point

Ingest a single data point from a source.

```http
POST /api/v1/ingest/single
```

**Request Body**:
```json
{
  "source_id": "sensor_001",
  "timestamp": "2026-02-18T10:30:00Z",
  "data_type": "temperature",
  "payload": {
    "value": 28.5,
    "unit": "celsius",
    "location": {
      "lat": 40.7128,
      "lon": -74.0060
    }
  },
  "quality_score": 0.98
}
```

**Response** (201 Created):
```json
{
  "status": "success",
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Ingest Batch

Ingest multiple data points in a single request.

```http
POST /api/v1/ingest/batch
```

**Request Body**:
```json
[
  {
    "source_id": "sensor_001",
    "timestamp": "2026-02-18T10:30:00Z",
    "data_type": "temperature",
    "payload": {"value": 28.5},
    "quality_score": 0.98
  },
  {
    "source_id": "sensor_002",
    "timestamp": "2026-02-18T10:30:00Z",
    "data_type": "humidity",
    "payload": {"value": 65.2},
    "quality_score": 0.95
  }
]
```

**Response** (200 OK):
```json
{
  "total": 2,
  "successful": 2,
  "failed": 0,
  "success_rate": 1.0
}
```

### WebSocket Streaming

Real-time data streaming via WebSocket.

```
WS /ws/stream/{stream_id}
```

**Example** (JavaScript):
```javascript
const ws = new WebSocket('wss://api.stratum-protocol.io/ws/stream/traffic_001');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

---

## Knowledge Graph API

**Base Path**: `/api/v1/graph`

### Add Infrastructure Node

Add a node to the urban knowledge graph.

```http
POST /api/v1/graph/nodes
```

**Request Body**:
```json
{
  "node_id": "power_station_01",
  "node_type": "power_grid",
  "name": "Central Power Station",
  "coordinates": [40.7128, -74.0060],
  "capacity": 5000.0,
  "current_load": 3500.0,
  "criticality_score": 0.85,
  "health_status": 0.92,
  "properties": {
    "voltage": "230kV",
    "operator": "City Power Authority",
    "commissioning_year": 2010
  }
}
```

**Response** (201 Created):
```json
{
  "status": "created",
  "node_id": "power_station_01"
}
```

### Add Dependency Edge

Create a dependency relationship between nodes.

```http
POST /api/v1/graph/edges
```

**Request Body**:
```json
{
  "source_node_id": "power_station_01",
  "target_node_id": "hospital_01",
  "relationship_type": "supplies_power",
  "strength": 0.9,
  "failure_propagation_prob": 0.75,
  "properties": {
    "transmission_line": "LINE_A1",
    "capacity_mw": 50
  }
}
```

### Get Node Neighbors

Retrieve neighboring nodes up to N hops away.

```http
GET /api/v1/graph/nodes/{node_id}/neighbors?max_depth=2
```

**Response** (200 OK):
```json
{
  "node_id": "power_station_01",
  "neighbors": [
    {
      "node_id": "hospital_01",
      "node_type": "healthcare",
      "name": "Central Hospital",
      "distance_hops": 1,
      "criticality_score": 0.95
    },
    {
      "node_id": "school_district_01",
      "node_type": "education",
      "name": "District 1 Schools",
      "distance_hops": 2,
      "criticality_score": 0.70
    }
  ],
  "count": 2
}
```

### Compute Criticality Scores

Run GNN-based criticality analysis.

```http
POST /api/v1/graph/criticality/compute
```

**Request Body**:
```json
{
  "node_ids": ["power_station_01", "water_pump_03"],
  "use_gnn": true,
  "update_scores": true
}
```

**Response** (200 OK):
```json
{
  "scores": {
    "power_station_01": 0.89,
    "water_pump_03": 0.76
  },
  "count": 2,
  "computation_time_ms": 150
}
```

### Get Critical Nodes

Retrieve the most critical nodes in the system.

```http
GET /api/v1/graph/critical-nodes?top_k=10
```

**Response** (200 OK):
```json
{
  "critical_nodes": [
    {
      "node_id": "power_station_01",
      "name": "Central Power Station",
      "criticality_score": 0.95,
      "reason": "Supplies power to 15 critical facilities"
    },
    {
      "node_id": "hospital_01",
      "name": "Central Hospital",
      "criticality_score": 0.93,
      "reason": "Primary emergency medical facility"
    }
  ],
  "count": 10
}
```

---

## Cascading Failure Simulation API

**Base Path**: `/api/v1/simulate`

### Run Cascade Simulation

Execute a Monte Carlo cascading failure simulation.

```http
POST /api/v1/simulate/cascade
```

**Request Body**:
```json
{
  "scenario_name": "Hurricane Category 4 Impact",
  "initial_failure_nodes": ["power_station_01", "transmission_tower_05"],
  "event_type": "hurricane",
  "event_severity": 0.85,
  "event_metadata": {
    "wind_speed_kmh": 250,
    "affected_area_km2": 500
  },
  "simulation_horizon_hours": 48,
  "monte_carlo_runs": 1000,
  "confidence_level": 0.95,
  "time_step_minutes": 5.0,
  "base_propagation_probability": 0.35,
  "load_threshold_multiplier": 1.3,
  "recovery_enabled": true,
  "mean_recovery_time_hours": 16.0,
  "temperature_celsius": 32.0,
  "wind_speed_kmh": 250.0,
  "precipitation_mm": 150.0
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "scenario_name": "Hurricane Category 4 Impact",
  "start_time": "2026-02-18T10:00:00Z",
  "end_time": "2026-02-18T10:05:32Z",
  "computation_time_seconds": 332.5,
  "total_affected_nodes": 47,
  "cascade_depth": 5,
  "mean_cascade_time_minutes": 125.3,
  "total_impact_score": 78.5,
  "cascade_probability": 0.87,
  "failure_probability_by_node": {
    "hospital_01": 0.92,
    "water_plant_02": 0.78,
    "telecom_hub_03": 0.65
  },
  "mean_time_to_failure_by_node": {
    "hospital_01": 45.2,
    "water_plant_02": 87.5,
    "telecom_hub_03": 152.1
  },
  "affected_nodes_ci": [42, 53],
  "impact_score_ci": [72.1, 84.9],
  "bottleneck_nodes": [
    "power_station_01",
    "transmission_tower_05",
    "substation_08"
  ],
  "critical_paths": [
    ["power_station_01", "hospital_01", "water_plant_02"],
    ["power_station_01", "telecom_hub_03", "emergency_center_01"],
    ["transmission_tower_05", "substation_08", "school_district_01"]
  ],
  "time_series_failures": [
    {
      "time": 0.0,
      "node_id": "power_station_01",
      "failure_prob": 1.0,
      "caused_by": null
    },
    {
      "time": 15.3,
      "node_id": "hospital_01",
      "failure_prob": 0.92,
      "caused_by": "power_station_01"
    }
  ],
  "recommendations": [
    "Critical: Reinforce node 'power_station_01' - identified as primary bottleneck",
    "High cascade risk (87.0%): Implement redundant pathways and load balancing",
    "Severe impact potential: Deploy rapid response teams",
    "Rapid cascade detected (avg 125.3 min): Implement automated failover systems"
  ]
}
```

### Get Simulation Result

Retrieve a previously run simulation by ID.

```http
GET /api/v1/simulations/{simulation_id}
```

**Response**: Same as simulation result above.

---

## Policy Simulation API

**Base Path**: `/api/v1/policy`

### Optimize Policy

Run multi-objective policy optimization.

```http
POST /api/v1/policy/optimize
```

**Request Body**:
```json
{
  "objective": "Maximize infrastructure resilience while minimizing cost",
  "candidate_actions": [
    {
      "action_type": "infrastructure_upgrade",
      "target_nodes": ["power_station_01"],
      "description": "Upgrade power station capacity",
      "estimated_cost_usd": 5000000,
      "implementation_time_days": 180,
      "expected_impact": {
        "resilience_increase": 0.25,
        "capacity_increase": 0.30
      }
    },
    {
      "action_type": "redundancy_creation",
      "target_nodes": ["hospital_01"],
      "description": "Install backup power system",
      "estimated_cost_usd": 1000000,
      "implementation_time_days": 90,
      "expected_impact": {
        "resilience_increase": 0.40,
        "independence_increase": 0.80
      }
    }
  ],
  "constraints": {
    "max_budget_usd": 10000000,
    "max_implementation_time_days": 365
  },
  "optimization_horizon_years": 10,
  "budget_usd": 10000000,
  "risk_tolerance": 0.3,
  "objectives_weights": {
    "resilience": 0.5,
    "cost": 0.3,
    "time": 0.2
  }
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "optimal_actions": [
    {
      "action_type": "redundancy_creation",
      "target_nodes": ["hospital_01"],
      "priority": 1,
      "expected_roi": 2.8
    },
    {
      "action_type": "infrastructure_upgrade",
      "target_nodes": ["power_station_01"],
      "priority": 2,
      "expected_roi": 1.9
    }
  ],
  "pareto_frontier": [
    {"resilience": 0.85, "cost": 6000000, "time": 180},
    {"resilience": 0.78, "cost": 4000000, "time": 120},
    {"resilience": 0.92, "cost": 10000000, "time": 365}
  ],
  "expected_outcomes": {
    "total_resilience_increase": 0.65,
    "total_cost_usd": 6000000,
    "total_time_days": 270,
    "net_present_value_usd": 15000000
  },
  "risk_metrics": {
    "value_at_risk_usd": 2000000,
    "expected_shortfall_usd": 500000,
    "failure_probability_reduction": 0.45
  },
  "cost_benefit_ratio": 2.5,
  "implementation_timeline": [
    {
      "phase": 1,
      "start_day": 0,
      "end_day": 90,
      "actions": ["redundancy_creation"],
      "budget": 1000000
    },
    {
      "phase": 2,
      "start_day": 90,
      "end_day": 270,
      "actions": ["infrastructure_upgrade"],
      "budget": 5000000
    }
  ],
  "computed_at": "2026-02-18T10:15:00Z"
}
```

---

## Decision Ledger API

**Base Path**: `/api/v1/ledger`

### Record Decision

Add a decision to the immutable ledger.

```http
POST /api/v1/ledger/decisions
```

**Request Body**:
```json
{
  "decision_id": "DEC-2026-02-18-001",
  "decision_type": "infrastructure_action",
  "description": "Deploy backup power to critical hospital",
  "rationale": "Simulation showed 92% failure probability during hurricanes",
  "proposed_by": "user_12345",
  "ai_recommendation": "APPROVE",
  "ai_confidence": 0.89,
  "ai_model_version": "cascade_sim_v1.2.3",
  "simulation_results_id": "550e8400-e29b-41d4-a716-446655440001",
  "tags": ["critical_infrastructure", "healthcare", "resilience"]
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "decision_id": "DEC-2026-02-18-001",
  "status": "proposed",
  "current_hash": "5a4d8e9f3c2b1a0e8d7c6b5a4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4",
  "signature": "3045022100...",
  "created_at": "2026-02-18T10:20:00Z",
  "verification_url": "/api/v1/ledger/decisions/DEC-2026-02-18-001/verify"
}
```

### Query Decisions

Query decisions from the ledger.

```http
GET /api/v1/ledger/decisions?status=executed&start_date=2026-02-01&limit=10
```

**Query Parameters**:
- `status`: Filter by status (proposed, approved, executed, etc.)
- `start_date`: Start date for time range
- `end_date`: End date for time range
- `tags`: Filter by tags (comma-separated)
- `limit`: Maximum results (default: 100)
- `offset`: Pagination offset

**Response** (200 OK):
```json
{
  "decisions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "decision_id": "DEC-2026-02-18-001",
      "status": "executed",
      "ai_confidence": 0.89,
      "executed_at": "2026-02-18T14:00:00Z",
      "actual_outcome": {
        "success": true,
        "measured_impact": 0.92
      },
      "prediction_accuracy": 0.97
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

### Verify Decision Integrity

Verify cryptographic integrity of a decision record.

```http
GET /api/v1/ledger/decisions/{decision_id}/verify
```

**Response** (200 OK):
```json
{
  "decision_id": "DEC-2026-02-18-001",
  "is_valid": true,
  "verification_details": {
    "hash_valid": true,
    "signature_valid": true,
    "chain_integrity": true,
    "timestamp_valid": true
  },
  "verified_at": "2026-02-18T10:25:00Z"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    },
    "timestamp": "2026-02-18T10:00:00Z",
    "request_id": "req_12345"
  }
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## Rate Limiting

API requests are rate limited per API key:

- **Free Tier**: 1,000 requests/hour
- **Professional**: 10,000 requests/hour
- **Enterprise**: Unlimited

Rate limit headers:
```
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 9523
X-RateLimit-Reset: 1708257600
```

---

## Webhooks

Configure webhooks to receive real-time notifications.

### Webhook Events

- `simulation.completed` - Simulation finished
- `alert.critical` - Critical alert triggered
- `decision.executed` - Decision executed
- `cascade.detected` - Cascade failure detected

### Webhook Payload Example

```json
{
  "event": "simulation.completed",
  "timestamp": "2026-02-18T10:30:00Z",
  "data": {
    "simulation_id": "550e8400-e29b-41d4-a716-446655440001",
    "scenario_name": "Hurricane Category 4 Impact",
    "status": "completed",
    "total_affected_nodes": 47
  }
}
```

---

**API Version**: 1.0.0  
**Last Updated**: 2026-02-18  
**Support**: api-support@stratum-protocol.io
