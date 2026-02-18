"""
STRATUM PROTOCOL - Cascading Failure Simulation Engine
Multi-hop graph traversal with RL-based stress propagation and Monte Carlo simulation
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
from uuid import UUID, uuid4
from collections import deque, defaultdict
from dataclasses import dataclass
from enum import Enum

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np
import torch
import torch.nn as nn
from scipy.stats import norm
import httpx
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# DATA MODELS
# =============================================================================

class FailureType(str, Enum):
    """Types of infrastructure failures"""
    OVERLOAD = "overload"
    PHYSICAL_DAMAGE = "physical_damage"
    CYBERATTACK = "cyberattack"
    HUMAN_ERROR = "human_error"
    CASCADE = "cascade"
    MAINTENANCE = "maintenance"


class EventType(str, Enum):
    """Types of triggering events"""
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    HURRICANE = "hurricane"
    HEATWAVE = "heatwave"
    CYBERATTACK = "cyberattack"
    POWER_OUTAGE = "power_outage"
    SYSTEM_FAILURE = "system_failure"


@dataclass
class FailureState:
    """State of a failed node during simulation"""
    node_id: str
    failure_type: FailureType
    failure_time: float  # Time in simulation (minutes)
    failure_probability: float
    impact_score: float
    caused_by: Optional[str] = None  # Parent node that caused this failure
    recovery_time: Optional[float] = None


class CascadeSimulationRequest(BaseModel):
    """Request for cascading failure simulation"""
    id: UUID = Field(default_factory=uuid4)
    scenario_name: str
    initial_failure_nodes: List[str]
    event_type: EventType
    event_severity: float = Field(..., ge=0, le=1)
    event_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Simulation parameters
    simulation_horizon_hours: int = Field(default=24, ge=1, le=168)
    monte_carlo_runs: int = Field(default=1000, ge=100, le=10000)
    confidence_level: float = Field(default=0.95, ge=0, le=1)
    time_step_minutes: float = Field(default=5.0, gt=0)
    
    # Failure propagation parameters
    base_propagation_probability: float = Field(default=0.3, ge=0, le=1)
    load_threshold_multiplier: float = Field(default=1.2, gt=1)
    recovery_enabled: bool = True
    mean_recovery_time_hours: float = Field(default=12.0, gt=0)
    
    # Climate/environmental modifiers
    temperature_celsius: Optional[float] = None
    wind_speed_kmh: Optional[float] = None
    precipitation_mm: Optional[float] = None


class CascadeSimulationResult(BaseModel):
    """Results from cascading failure simulation"""
    id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    scenario_name: str
    
    # Execution metadata
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    computation_time_seconds: Optional[float] = None
    
    # Aggregate results
    total_affected_nodes: int
    cascade_depth: int  # Maximum propagation hops
    mean_cascade_time_minutes: float
    total_impact_score: float
    
    # Statistical results across Monte Carlo runs
    failure_probability_by_node: Dict[str, float]
    mean_time_to_failure_by_node: Dict[str, float]
    cascade_probability: float
    
    # Confidence intervals
    affected_nodes_ci: Tuple[int, int]  # (lower, upper) bounds
    impact_score_ci: Tuple[float, float]
    
    # Critical analysis
    bottleneck_nodes: List[str]  # High-centrality failure points
    critical_paths: List[List[str]]  # Most likely cascade paths
    failure_tree: Optional[Dict[str, Any]] = None
    
    # Time series
    time_series_failures: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)


class StressState(BaseModel):
    """Current stress state of infrastructure"""
    node_id: str
    load_ratio: float = Field(..., ge=0)
    health_status: float = Field(..., ge=0, le=1)
    failure_probability: float = Field(..., ge=0, le=1)
    stress_level: float = Field(..., ge=0, le=1)


# =============================================================================
# REINFORCEMENT LEARNING MODEL
# =============================================================================

class CascadeRL(nn.Module):
    """
    Reinforcement Learning model for predicting cascade propagation
    Uses Actor-Critic architecture to learn failure patterns
    """
    
    def __init__(self, state_dim: int = 32, action_dim: int = 2, hidden_dim: int = 128):
        super(CascadeRL, self).__init__()
        
        # Actor network (propagation policy)
        self.actor = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim),
            nn.Softmax(dim=-1)
        )
        
        # Critic network (value estimation)
        self.critic = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
    
    def forward(self, state):
        """
        Forward pass
        
        Args:
            state: Current state tensor [batch, state_dim]
            
        Returns:
            action_probs: Propagation probabilities
            value: State value estimation
        """
        action_probs = self.actor(state)
        value = self.critic(state)
        return action_probs, value
    
    def get_propagation_probability(self, state_features: np.ndarray) -> float:
        """Get propagation probability for given state"""
        with torch.no_grad():
            state_tensor = torch.tensor(state_features, dtype=torch.float32).unsqueeze(0)
            action_probs, _ = self.forward(state_tensor)
            # Return probability of propagation (action = 1)
            return float(action_probs[0, 1].item())


# =============================================================================
# CASCADING FAILURE SIMULATION ENGINE
# =============================================================================

class CascadingFailureEngine:
    """Engine for simulating cascading infrastructure failures"""
    
    def __init__(self, knowledge_graph_url: str):
        self.knowledge_graph_url = knowledge_graph_url
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # RL model for learning failure patterns
        self.rl_model = CascadeRL(state_dim=32, action_dim=2)
        # In production: self.rl_model.load_state_dict(torch.load('models/cascade_rl.pt'))
        self.rl_model.eval()
        
        logger.info("Cascading Failure Engine initialized")
    
    async def simulate_cascade(
        self,
        request: CascadeSimulationRequest
    ) -> CascadeSimulationResult:
        """
        Run Monte Carlo cascading failure simulation
        
        Performs multiple simulation runs to estimate probability distributions
        and confidence intervals for cascade outcomes
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting cascade simulation: {request.scenario_name}")
        
        # Fetch infrastructure graph context
        graph_data = await self._fetch_graph_context(request.initial_failure_nodes)
        
        # Run Monte Carlo simulations
        mc_results = []
        for run_idx in range(request.monte_carlo_runs):
            result = await self._run_single_cascade_simulation(request, graph_data)
            mc_results.append(result)
            
            if (run_idx + 1) % 100 == 0:
                logger.info(f"Completed {run_idx + 1}/{request.monte_carlo_runs} simulations")
        
        # Aggregate results
        aggregated = self._aggregate_monte_carlo_results(mc_results, request)
        
        # Analyze critical paths and bottlenecks
        aggregated.bottleneck_nodes = self._identify_bottlenecks(mc_results, graph_data)
        aggregated.critical_paths = self._extract_critical_paths(mc_results)
        aggregated.failure_tree = self._build_failure_tree(mc_results)
        
        # Generate recommendations
        aggregated.recommendations = self._generate_recommendations(aggregated, request)
        
        # Finalize metadata
        end_time = datetime.utcnow()
        aggregated.end_time = end_time
        aggregated.computation_time_seconds = (end_time - start_time).total_seconds()
        
        logger.info(f"Simulation completed: {aggregated.total_affected_nodes} nodes affected")
        
        return aggregated
    
    async def _fetch_graph_context(self, node_ids: List[str]) -> Dict[str, Any]:
        """Fetch relevant graph data from Knowledge Graph Service"""
        graph_data = {
            "nodes": {},
            "edges": [],
            "adjacency": defaultdict(list)
        }
        
        try:
            # Fetch each initial node and its neighbors
            for node_id in node_ids:
                # Get node details
                response = await self.http_client.get(
                    f"{self.knowledge_graph_url}/api/v1/graph/nodes/{node_id}"
                )
                if response.status_code == 200:
                    node_data = response.json()
                    graph_data["nodes"][node_id] = node_data
                
                # Get neighbors (up to 3 hops)
                response = await self.http_client.get(
                    f"{self.knowledge_graph_url}/api/v1/graph/nodes/{node_id}/neighbors",
                    params={"max_depth": 3}
                )
                if response.status_code == 200:
                    neighbors_data = response.json()
                    for neighbor in neighbors_data.get("neighbors", []):
                        neighbor_id = neighbor["node_id"]
                        if neighbor_id not in graph_data["nodes"]:
                            graph_data["nodes"][neighbor_id] = neighbor
                        graph_data["adjacency"][node_id].append(neighbor_id)
            
            logger.info(f"Fetched graph context: {len(graph_data['nodes'])} nodes")
            
        except Exception as e:
            logger.error(f"Error fetching graph context: {e}")
        
        return graph_data
    
    async def _run_single_cascade_simulation(
        self,
        request: CascadeSimulationRequest,
        graph_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a single cascade simulation instance
        
        Uses BFS-like propagation with stochastic failure determination
        """
        # Initialize simulation state
        failed_nodes: Dict[str, FailureState] = {}
        stressed_nodes: Set[str] = set()
        current_time = 0.0
        max_time = request.simulation_horizon_hours * 60  # Convert to minutes
        
        # Initialize with starting failures
        failure_queue = deque()
        for node_id in request.initial_failure_nodes:
            failure_state = FailureState(
                node_id=node_id,
                failure_type=FailureType.PHYSICAL_DAMAGE,
                failure_time=0.0,
                failure_probability=1.0,
                impact_score=1.0
            )
            failed_nodes[node_id] = failure_state
            failure_queue.append((node_id, 0.0))
        
        # Time series tracking
        time_series = []
        cascade_depth = 0
        
        # Propagate failures through network
        while failure_queue and current_time < max_time:
            node_id, failure_time = failure_queue.popleft()
            
            # Get neighbors
            neighbors = graph_data["adjacency"].get(node_id, [])
            cascade_depth = max(cascade_depth, len(failed_nodes))
            
            for neighbor_id in neighbors:
                # Skip if already failed
                if neighbor_id in failed_nodes:
                    continue
                
                # Get neighbor node data
                neighbor_data = graph_data["nodes"].get(neighbor_id)
                if not neighbor_data:
                    continue
                
                # Calculate failure probability
                failure_prob = self._calculate_failure_probability(
                    neighbor_data,
                    failed_nodes,
                    request,
                    current_time
                )
                
                # Stochastic failure determination
                if np.random.random() < failure_prob:
                    # Calculate time to failure
                    time_to_failure = self._calculate_time_to_failure(
                        failure_prob,
                        request.time_step_minutes
                    )
                    
                    failure_state = FailureState(
                        node_id=neighbor_id,
                        failure_type=FailureType.CASCADE,
                        failure_time=current_time + time_to_failure,
                        failure_probability=failure_prob,
                        impact_score=self._calculate_impact_score(neighbor_data),
                        caused_by=node_id
                    )
                    
                    failed_nodes[neighbor_id] = failure_state
                    failure_queue.append((neighbor_id, failure_state.failure_time))
                    
                    # Record in time series
                    time_series.append({
                        "time": failure_state.failure_time,
                        "node_id": neighbor_id,
                        "failure_prob": failure_prob,
                        "caused_by": node_id
                    })
            
            current_time += request.time_step_minutes
        
        # Calculate aggregate metrics
        total_impact = sum(fs.impact_score for fs in failed_nodes.values())
        mean_time = np.mean([fs.failure_time for fs in failed_nodes.values()]) if failed_nodes else 0
        
        return {
            "failed_nodes": failed_nodes,
            "cascade_depth": cascade_depth,
            "total_impact": total_impact,
            "mean_cascade_time": mean_time,
            "time_series": time_series,
            "stressed_nodes": list(stressed_nodes)
        }
    
    def _calculate_failure_probability(
        self,
        node_data: Dict[str, Any],
        failed_nodes: Dict[str, FailureState],
        request: CascadeSimulationRequest,
        current_time: float
    ) -> float:
        """
        Calculate failure probability for a node given current state
        
        Factors:
        - Load ratio and capacity
        - Number of failed dependencies
        - Event severity
        - Environmental conditions
        - RL model prediction
        """
        # Base probability from request
        base_prob = request.base_propagation_probability
        
        # Load factor
        capacity = node_data.get("capacity", 1.0) or 1.0
        current_load = node_data.get("current_load", 0.0) or 0.0
        load_ratio = current_load / capacity if capacity > 0 else 0
        
        if load_ratio > request.load_threshold_multiplier:
            load_factor = 1.5
        elif load_ratio > 0.8:
            load_factor = 1.2
        else:
            load_factor = 1.0
        
        # Dependency factor (more failed neighbors = higher probability)
        # In production, this would use actual graph structure
        dependency_factor = 1.0 + (len(failed_nodes) * 0.1)
        
        # Event severity factor
        severity_factor = 1.0 + request.event_severity
        
        # Environmental factors
        env_factor = 1.0
        if request.temperature_celsius and request.temperature_celsius > 35:
            env_factor *= 1.2  # Heat stress
        if request.wind_speed_kmh and request.wind_speed_kmh > 50:
            env_factor *= 1.3  # High winds
        
        # RL model prediction
        state_features = self._extract_state_features(
            node_data,
            failed_nodes,
            current_time
        )
        rl_prob = self.rl_model.get_propagation_probability(state_features)
        
        # Combine factors
        combined_prob = (
            base_prob * 
            load_factor * 
            dependency_factor * 
            severity_factor * 
            env_factor *
            rl_prob
        )
        
        return min(combined_prob, 1.0)
    
    def _extract_state_features(
        self,
        node_data: Dict[str, Any],
        failed_nodes: Dict[str, FailureState],
        current_time: float
    ) -> np.ndarray:
        """Extract state features for RL model"""
        features = np.zeros(32)
        
        capacity = node_data.get("capacity", 1.0) or 1.0
        current_load = node_data.get("current_load", 0.0) or 0.0
        
        features[0] = current_load / capacity if capacity > 0 else 0
        features[1] = node_data.get("health_status", 1.0)
        features[2] = node_data.get("criticality_score", 0.5)
        features[3] = len(failed_nodes) / 100.0  # Normalized
        features[4] = current_time / 1440.0  # Normalized to 24 hours
        features[5] = 1.0 if capacity > 1000 else 0.0
        
        # Additional engineered features
        features[6:] = np.random.randn(26) * 0.1  # Placeholder
        
        return features
    
    def _calculate_time_to_failure(
        self,
        failure_prob: float,
        time_step: float
    ) -> float:
        """Calculate time until failure occurs (exponential distribution)"""
        # Use exponential distribution with rate proportional to probability
        rate = failure_prob * 0.1  # Scaling factor
        time_to_failure = np.random.exponential(1.0 / rate) if rate > 0 else time_step
        return max(time_step, time_to_failure)
    
    def _calculate_impact_score(self, node_data: Dict[str, Any]) -> float:
        """Calculate impact score of node failure"""
        criticality = node_data.get("criticality_score", 0.5)
        capacity = node_data.get("capacity", 1.0) or 1.0
        
        # Normalize capacity to [0, 1] range (assuming max capacity ~10000)
        normalized_capacity = min(capacity / 10000.0, 1.0)
        
        impact = (criticality * 0.7) + (normalized_capacity * 0.3)
        return impact
    
    def _aggregate_monte_carlo_results(
        self,
        mc_results: List[Dict[str, Any]],
        request: CascadeSimulationRequest
    ) -> CascadeSimulationResult:
        """Aggregate results from multiple Monte Carlo runs"""
        
        # Collect statistics
        affected_counts = [len(r["failed_nodes"]) for r in mc_results]
        impact_scores = [r["total_impact"] for r in mc_results]
        cascade_depths = [r["cascade_depth"] for r in mc_results]
        cascade_times = [r["mean_cascade_time"] for r in mc_results]
        
        # Calculate node-level statistics
        node_failure_counts = defaultdict(int)
        node_failure_times = defaultdict(list)
        
        for result in mc_results:
            for node_id, failure_state in result["failed_nodes"].items():
                node_failure_counts[node_id] += 1
                node_failure_times[node_id].append(failure_state.failure_time)
        
        # Calculate failure probabilities
        num_runs = len(mc_results)
        failure_probs = {
            node_id: count / num_runs
            for node_id, count in node_failure_counts.items()
        }
        
        # Calculate mean time to failure
        mean_times = {
            node_id: np.mean(times)
            for node_id, times in node_failure_times.items()
        }
        
        # Calculate confidence intervals
        alpha = 1 - request.confidence_level
        affected_ci = (
            int(np.percentile(affected_counts, alpha / 2 * 100)),
            int(np.percentile(affected_counts, (1 - alpha / 2) * 100))
        )
        impact_ci = (
            float(np.percentile(impact_scores, alpha / 2 * 100)),
            float(np.percentile(impact_scores, (1 - alpha / 2) * 100))
        )
        
        # Cascade probability (probability that cascade extends beyond initial nodes)
        cascade_occurred = sum(1 for r in mc_results if len(r["failed_nodes"]) > len(request.initial_failure_nodes))
        cascade_prob = cascade_occurred / num_runs
        
        result = CascadeSimulationResult(
            request_id=request.id,
            scenario_name=request.scenario_name,
            total_affected_nodes=int(np.mean(affected_counts)),
            cascade_depth=int(np.mean(cascade_depths)),
            mean_cascade_time_minutes=float(np.mean(cascade_times)),
            total_impact_score=float(np.mean(impact_scores)),
            failure_probability_by_node=failure_probs,
            mean_time_to_failure_by_node=mean_times,
            cascade_probability=cascade_prob,
            affected_nodes_ci=affected_ci,
            impact_score_ci=impact_ci,
            time_series_failures=mc_results[0]["time_series"]  # Representative run
        )
        
        return result
    
    def _identify_bottlenecks(
        self,
        mc_results: List[Dict[str, Any]],
        graph_data: Dict[str, Any]
    ) -> List[str]:
        """Identify critical bottleneck nodes"""
        # Nodes that appear in most simulations with early failure times
        node_importance = defaultdict(float)
        
        for result in mc_results:
            for node_id, failure_state in result["failed_nodes"].items():
                # Weight by inverse of failure time (early failures more critical)
                importance = 1.0 / (failure_state.failure_time + 1)
                node_importance[node_id] += importance
        
        # Sort by importance
        sorted_nodes = sorted(
            node_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [node_id for node_id, _ in sorted_nodes[:10]]
    
    def _extract_critical_paths(
        self,
        mc_results: List[Dict[str, Any]]
    ) -> List[List[str]]:
        """Extract most common cascade paths"""
        # Count path frequencies
        path_counts = defaultdict(int)
        
        for result in mc_results:
            # Reconstruct paths from failure tree
            paths = self._reconstruct_paths(result["failed_nodes"])
            for path in paths:
                path_tuple = tuple(path)
                path_counts[path_tuple] += 1
        
        # Return top 5 most common paths
        sorted_paths = sorted(
            path_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [list(path) for path, _ in sorted_paths[:5]]
    
    def _reconstruct_paths(
        self,
        failed_nodes: Dict[str, FailureState]
    ) -> List[List[str]]:
        """Reconstruct failure paths from node states"""
        paths = []
        
        # Find leaf nodes (nodes that didn't cause further failures)
        caused_by_map = {fs.node_id: fs.caused_by for fs in failed_nodes.values()}
        leaf_nodes = [
            node_id for node_id in failed_nodes.keys()
            if node_id not in caused_by_map.values()
        ]
        
        # Trace back from each leaf
        for leaf in leaf_nodes:
            path = [leaf]
            current = leaf
            
            while caused_by_map.get(current):
                parent = caused_by_map[current]
                path.insert(0, parent)
                current = parent
            
            paths.append(path)
        
        return paths
    
    def _build_failure_tree(
        self,
        mc_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build hierarchical failure tree structure"""
        # Aggregate failure relationships across all runs
        tree = {"root": {"children": []}}
        
        # Use first simulation as representative
        if mc_results:
            failed_nodes = mc_results[0]["failed_nodes"]
            
            # Build tree from relationships
            for node_id, failure_state in failed_nodes.items():
                if not failure_state.caused_by:
                    tree["root"]["children"].append({
                        "node_id": node_id,
                        "failure_time": failure_state.failure_time,
                        "impact": failure_state.impact_score
                    })
        
        return tree
    
    def _generate_recommendations(
        self,
        result: CascadeSimulationResult,
        request: CascadeSimulationRequest
    ) -> List[str]:
        """Generate actionable recommendations based on simulation"""
        recommendations = []
        
        # Recommendation 1: Address bottlenecks
        if result.bottleneck_nodes:
            top_bottleneck = result.bottleneck_nodes[0]
            recommendations.append(
                f"Critical: Reinforce node '{top_bottleneck}' - identified as primary bottleneck with highest cascade risk"
            )
        
        # Recommendation 2: Cascade probability
        if result.cascade_probability > 0.7:
            recommendations.append(
                f"High cascade risk ({result.cascade_probability:.1%}): Implement redundant pathways and load balancing"
            )
        
        # Recommendation 3: Impact mitigation
        if result.total_impact_score > 50:
            recommendations.append(
                "Severe impact potential: Deploy rapid response teams and establish emergency protocols"
            )
        
        # Recommendation 4: Time-based
        if result.mean_cascade_time_minutes < 30:
            recommendations.append(
                f"Rapid cascade detected (avg {result.mean_cascade_time_minutes:.1f} min): Implement automated failover systems"
            )
        
        # Recommendation 5: Recovery
        if request.recovery_enabled:
            recommendations.append(
                "Enable proactive maintenance for high-risk nodes identified in simulation"
            )
        
        return recommendations


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

engine: Optional[CascadingFailureEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    engine = CascadingFailureEngine(
        knowledge_graph_url="http://knowledge-graph:8002"
    )
    yield
    if engine:
        await engine.http_client.aclose()

app = FastAPI(
    title="STRATUM PROTOCOL - Cascading Failure Simulation",
    description="Multi-hop failure propagation with RL and Monte Carlo simulation",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "cascading-failure"}

@app.post("/api/v1/simulate/cascade", response_model=CascadeSimulationResult)
async def simulate_cascade(request: CascadeSimulationRequest):
    """Run cascading failure simulation"""
    if not engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    result = await engine.simulate_cascade(request)
    return result

@app.get("/api/v1/simulations/{simulation_id}")
async def get_simulation_result(simulation_id: UUID):
    """Get simulation result by ID"""
    # In production, retrieve from database
    raise HTTPException(status_code=501, detail="Not implemented")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
