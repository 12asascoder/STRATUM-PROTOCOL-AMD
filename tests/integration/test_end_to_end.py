"""
Integration tests for STRATUM PROTOCOL
Tests end-to-end flow across all microservices
"""
import pytest
import requests
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"  # API Gateway

class TestDataIngestionFlow:
    """Test data ingestion pipeline"""
    
    def test_ingest_single_datapoint(self):
        """Test single data point ingestion"""
        payload = {
            "source_id": "test-sensor-001",
            "source_type": "iot_sensor",
            "node_id": "POWER_GRID_001",
            "timestamp": "2024-01-15T10:00:00Z",
            "data": {
                "load": 0.75,
                "voltage": 230.5,
                "temperature": 45.2
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ingest/single",
            json=payload,
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data_point_id" in data
    
    def test_batch_ingestion(self):
        """Test batch ingestion"""
        batch = [
            {
                "source_id": f"sensor-{i:03d}",
                "source_type": "iot_sensor",
                "node_id": f"NODE_{i:03d}",
                "timestamp": "2024-01-15T10:00:00Z",
                "data": {"value": i * 10}
            }
            for i in range(100)
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ingest/batch",
            json={"data_points": batch},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["successful"] == 100

class TestKnowledgeGraphFlow:
    """Test knowledge graph operations"""
    
    def test_create_and_query_node(self):
        """Test node creation and retrieval"""
        # Create node
        node_payload = {
            "node_id": "TEST_POWER_001",
            "name": "Test Power Station",
            "node_type": "power_generation",
            "location": {"lat": 40.7128, "lon": -74.0060},
            "capacity": 1000.0,
            "current_load": 750.0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/graph/nodes",
            json=node_payload,
            timeout=10
        )
        
        assert response.status_code == 200
        
        # Query node
        response = requests.get(
            f"{BASE_URL}/api/v1/graph/nodes/TEST_POWER_001",
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["node_id"] == "TEST_POWER_001"
    
    def test_compute_criticality(self):
        """Test GNN-based criticality scoring"""
        response = requests.post(
            f"{BASE_URL}/api/v1/graph/criticality/compute",
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "criticality_scores" in data

class TestCascadeSimulationFlow:
    """Test cascading failure simulation"""
    
    def test_cascade_simulation(self):
        """Test Monte Carlo cascade simulation"""
        payload = {
            "initial_failure_nodes": ["POWER_GRID_001"],
            "monte_carlo_runs": 100,
            "confidence_level": 0.95,
            "environmental_factors": {
                "temperature": 35.0,
                "wind_speed": 15.0
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/simulate/cascade",
            json=payload,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "affected_nodes_ci" in data
        assert "bottleneck_nodes" in data
        assert "critical_paths" in data

class TestPolicyOptimizationFlow:
    """Test policy optimization"""
    
    def test_policy_optimization(self):
        """Test multi-objective optimization"""
        payload = {
            "objectives": [
                "minimize_casualties",
                "minimize_cost",
                "maximize_resilience"
            ],
            "constraints": {
                "max_budget": 1000000,
                "max_time": 30
            },
            "candidate_actions": [
                {
                    "policy_type": "infrastructure",
                    "parameters": {"upgrade_capacity": 1.5},
                    "cost": 500000,
                    "implementation_time": 20
                }
            ],
            "simulation_scenarios": ["scenario_001"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/optimize/policies",
            json=payload,
            timeout=120
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "pareto_rank" in data[0]

class TestDecisionLedgerFlow:
    """Test cryptographic decision ledger"""
    
    def test_add_and_verify_decision(self):
        """Test adding decision and verifying chain"""
        # Add decision
        decision_payload = {
            "decision_type": "infrastructure_upgrade",
            "parameters": {"node_id": "POWER_001", "action": "upgrade"},
            "outcomes": {"success": True, "cost": 100000},
            "authority": "system_admin"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/ledger/decisions",
            json=decision_payload,
            timeout=10
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "current_hash" in data
        assert "previous_hash" in data
        
        # Verify chain
        response = requests.get(
            f"{BASE_URL}/api/v1/ledger/verify",
            timeout=10
        )
        
        assert response.status_code == 200
        verification = response.json()
        assert verification["is_valid"] == True

class TestEndToEndFlow:
    """Test complete end-to-end workflow"""
    
    def test_full_decision_pipeline(self):
        """Test: Ingest → Graph → Simulate → Optimize → Ledger"""
        
        # Step 1: Ingest data
        ingest_response = requests.post(
            f"{BASE_URL}/api/v1/ingest/single",
            json={
                "source_id": "e2e-test",
                "source_type": "event",
                "node_id": "CRITICAL_NODE_001",
                "data": {"event_type": "failure", "severity": "high"}
            },
            timeout=10
        )
        assert ingest_response.status_code == 200
        
        time.sleep(2)  # Allow propagation
        
        # Step 2: Run cascade simulation
        sim_response = requests.post(
            f"{BASE_URL}/api/v1/simulate/cascade",
            json={
                "initial_failure_nodes": ["CRITICAL_NODE_001"],
                "monte_carlo_runs": 50
            },
            timeout=60
        )
        assert sim_response.status_code == 200
        simulation_result = sim_response.json()
        
        # Step 3: Optimize policy
        policy_response = requests.post(
            f"{BASE_URL}/api/v1/optimize/policies",
            json={
                "objectives": ["minimize_casualties"],
                "constraints": {"max_budget": 1000000},
                "candidate_actions": [{
                    "policy_type": "emergency",
                    "parameters": {"evacuate": True},
                    "cost": 50000,
                    "implementation_time": 1
                }],
                "simulation_scenarios": ["current"]
            },
            timeout=90
        )
        assert policy_response.status_code == 200
        
        # Step 4: Log decision to ledger
        best_policy = policy_response.json()[0]
        ledger_response = requests.post(
            f"{BASE_URL}/api/v1/ledger/decisions",
            json={
                "decision_type": "emergency_response",
                "parameters": {"simulation_id": simulation_result["simulation_id"]},
                "outcomes": {"policy_selected": best_policy["action_id"]},
                "authority": "automated_system"
            },
            timeout=10
        )
        assert ledger_response.status_code == 200
        
        # Verify end-to-end success
        decision = ledger_response.json()
        assert decision["current_hash"] != ""

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
