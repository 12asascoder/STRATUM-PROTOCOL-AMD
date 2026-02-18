"""
Performance/Load testing with Locust
Simulates high-load scenarios for STRATUM PROTOCOL
"""
from locust import HttpUser, task, between
import random

class StratumProtocolUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize user session"""
        self.node_ids = [f"NODE_{i:04d}" for i in range(1000)]
    
    @task(3)
    def ingest_data(self):
        """Simulate data ingestion (most frequent operation)"""
        payload = {
            "source_id": f"sensor-{random.randint(1, 1000)}",
            "source_type": "iot_sensor",
            "node_id": random.choice(self.node_ids),
            "data": {
                "load": random.uniform(0, 1),
                "temperature": random.uniform(20, 60)
            }
        }
        
        with self.client.post(
            "/api/v1/ingest/single",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Ingestion failed: {response.status_code}")
    
    @task(2)
    def query_graph(self):
        """Query knowledge graph"""
        node_id = random.choice(self.node_ids)
        
        with self.client.get(
            f"/api/v1/graph/nodes/{node_id}",
            catch_response=True
        ) as response:
            if response.status_code == 404:
                response.success()  # Node not found is acceptable
            elif response.status_code != 200:
                response.failure(f"Query failed: {response.status_code}")
    
    @task(1)
    def run_simulation(self):
        """Run cascade simulation (resource-intensive)"""
        payload = {
            "initial_failure_nodes": [random.choice(self.node_ids)],
            "monte_carlo_runs": 10,  # Reduced for load testing
            "confidence_level": 0.95
        }
        
        with self.client.post(
            "/api/v1/simulate/cascade",
            json=payload,
            catch_response=True,
            timeout=30
        ) as response:
            if response.status_code != 200:
                response.failure(f"Simulation failed: {response.status_code}")
    
    @task(1)
    def query_ledger(self):
        """Query decision ledger"""
        with self.client.get(
            "/api/v1/ledger/decisions?limit=10",
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"Ledger query failed: {response.status_code}")
