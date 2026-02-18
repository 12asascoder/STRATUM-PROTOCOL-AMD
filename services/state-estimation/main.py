"""
STRATUM PROTOCOL - State Estimation Engine
Bayesian inference for infrastructure state estimation with uncertainty quantification
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np
from scipy.stats import norm, multivariate_normal
from scipy.linalg import inv
import torch
import httpx
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# DATA MODELS
# =============================================================================

class StateEstimationRequest(BaseModel):
    """Request for state estimation"""
    node_ids: List[str]
    sensor_data: List[Dict[str, Any]]
    estimation_type: str = "kalman"  # kalman, particle, bayesian
    uncertainty_quantification: bool = True


class StateEstimation(BaseModel):
    """Estimated state of infrastructure"""
    node_id: str
    estimated_load: float
    estimated_health: float
    stress_score: float
    failure_probability: float
    uncertainty: Dict[str, float]
    confidence_interval: Tuple[float, float]
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class KalmanFilter:
    """Kalman filter for time-series state estimation"""
    
    def __init__(self, state_dim: int = 4, measurement_dim: int = 2):
        self.state_dim = state_dim
        self.measurement_dim = measurement_dim
        
        # State transition matrix
        self.A = np.eye(state_dim)
        self.A[0, 2] = 1.0  # position-velocity coupling
        self.A[1, 3] = 1.0
        
        # Measurement matrix
        self.H = np.zeros((measurement_dim, state_dim))
        self.H[0, 0] = 1.0
        self.H[1, 1] = 1.0
        
        # Process noise covariance
        self.Q = np.eye(state_dim) * 0.01
        
        # Measurement noise covariance
        self.R = np.eye(measurement_dim) * 0.1
        
        # Initial state and covariance
        self.x = np.zeros(state_dim)
        self.P = np.eye(state_dim)
    
    def predict(self) -> np.ndarray:
        """Prediction step"""
        self.x = self.A @ self.x
        self.P = self.A @ self.P @ self.A.T + self.Q
        return self.x
    
    def update(self, measurement: np.ndarray) -> np.ndarray:
        """Update step"""
        # Innovation
        y = measurement - self.H @ self.x
        
        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman gain
        K = self.P @ self.H.T @ inv(S)
        
        # State update
        self.x = self.x + K @ y
        
        # Covariance update
        self.P = (np.eye(self.state_dim) - K @ self.H) @ self.P
        
        return self.x


class StateEstimationEngine:
    """Engine for Bayesian state estimation"""
    
    def __init__(self, knowledge_graph_url: str):
        self.knowledge_graph_url = knowledge_graph_url
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Kalman filters for each node
        self.filters: Dict[str, KalmanFilter] = {}
        
        logger.info("State Estimation Engine initialized")
    
    async def estimate_states(
        self,
        request: StateEstimationRequest
    ) -> List[StateEstimation]:
        """Estimate states for multiple nodes"""
        
        estimations = []
        
        for node_id in request.node_ids:
            # Get historical data
            node_data = await self._get_node_data(node_id)
            
            # Initialize filter if needed
            if node_id not in self.filters:
                self.filters[node_id] = KalmanFilter()
            
            # Get sensor measurements
            measurements = self._extract_measurements(request.sensor_data, node_id)
            
            # Run estimation
            if request.estimation_type == "kalman":
                estimation = await self._kalman_estimation(node_id, measurements, node_data)
            elif request.estimation_type == "bayesian":
                estimation = await self._bayesian_estimation(node_id, measurements, node_data)
            else:
                estimation = await self._particle_filter_estimation(node_id, measurements, node_data)
            
            estimations.append(estimation)
        
        return estimations
    
    async def _kalman_estimation(
        self,
        node_id: str,
        measurements: np.ndarray,
        node_data: Dict[str, Any]
    ) -> StateEstimation:
        """Kalman filter-based estimation"""
        
        kf = self.filters[node_id]
        
        # Predict
        predicted_state = kf.predict()
        
        # Update with measurement if available
        if measurements is not None and len(measurements) > 0:
            updated_state = kf.update(measurements[-1])
        else:
            updated_state = predicted_state
        
        # Extract estimates
        estimated_load = float(updated_state[0])
        estimated_health = float(updated_state[1])
        
        # Calculate stress score
        capacity = node_data.get("capacity", 1.0)
        stress_score = min(estimated_load / capacity, 1.0) if capacity > 0 else 0.0
        
        # Calculate failure probability
        failure_prob = self._calculate_failure_probability(stress_score, estimated_health)
        
        # Uncertainty from covariance
        uncertainty = {
            "load": float(np.sqrt(kf.P[0, 0])),
            "health": float(np.sqrt(kf.P[1, 1]))
        }
        
        # 95% confidence interval
        ci_load = (
            estimated_load - 1.96 * uncertainty["load"],
            estimated_load + 1.96 * uncertainty["load"]
        )
        
        return StateEstimation(
            node_id=node_id,
            estimated_load=max(0, estimated_load),
            estimated_health=max(0, min(1, estimated_health)),
            stress_score=stress_score,
            failure_probability=failure_prob,
            uncertainty=uncertainty,
            confidence_interval=ci_load
        )
    
    async def _bayesian_estimation(
        self,
        node_id: str,
        measurements: np.ndarray,
        node_data: Dict[str, Any]
    ) -> StateEstimation:
        """Bayesian inference-based estimation"""
        
        # Prior distribution (from historical data)
        prior_mean = np.array([node_data.get("current_load", 0.0), 
                               node_data.get("health_status", 1.0)])
        prior_cov = np.eye(2) * 0.1
        
        # Likelihood (from measurements)
        if measurements is not None and len(measurements) > 0:
            measurement_mean = measurements[-1]
            measurement_cov = np.eye(2) * 0.05
            
            # Posterior (Bayesian update)
            posterior_cov_inv = inv(prior_cov) + inv(measurement_cov)
            posterior_cov = inv(posterior_cov_inv)
            posterior_mean = posterior_cov @ (
                inv(prior_cov) @ prior_mean + 
                inv(measurement_cov) @ measurement_mean
            )
        else:
            posterior_mean = prior_mean
            posterior_cov = prior_cov
        
        estimated_load = float(posterior_mean[0])
        estimated_health = float(posterior_mean[1])
        
        capacity = node_data.get("capacity", 1.0)
        stress_score = min(estimated_load / capacity, 1.0) if capacity > 0 else 0.0
        failure_prob = self._calculate_failure_probability(stress_score, estimated_health)
        
        uncertainty = {
            "load": float(np.sqrt(posterior_cov[0, 0])),
            "health": float(np.sqrt(posterior_cov[1, 1]))
        }
        
        ci_load = (
            estimated_load - 1.96 * uncertainty["load"],
            estimated_load + 1.96 * uncertainty["load"]
        )
        
        return StateEstimation(
            node_id=node_id,
            estimated_load=max(0, estimated_load),
            estimated_health=max(0, min(1, estimated_health)),
            stress_score=stress_score,
            failure_probability=failure_prob,
            uncertainty=uncertainty,
            confidence_interval=ci_load
        )
    
    async def _particle_filter_estimation(
        self,
        node_id: str,
        measurements: np.ndarray,
        node_data: Dict[str, Any]
    ) -> StateEstimation:
        """Particle filter for non-linear estimation"""
        
        num_particles = 1000
        
        # Initialize particles
        particles = np.random.randn(num_particles, 2)
        particles[:, 0] = particles[:, 0] * 10 + node_data.get("current_load", 0.0)
        particles[:, 1] = np.abs(particles[:, 1] * 0.1 + node_data.get("health_status", 1.0))
        
        # Weights
        weights = np.ones(num_particles) / num_particles
        
        if measurements is not None and len(measurements) > 0:
            # Update weights based on likelihood
            for i in range(num_particles):
                likelihood = multivariate_normal.pdf(
                    measurements[-1],
                    mean=particles[i],
                    cov=np.eye(2) * 0.1
                )
                weights[i] *= likelihood
            
            # Normalize weights
            weights += 1e-300  # Avoid division by zero
            weights /= np.sum(weights)
            
            # Resample
            indices = np.random.choice(num_particles, num_particles, p=weights)
            particles = particles[indices]
        
        # Estimate from particles
        estimated_load = float(np.mean(particles[:, 0]))
        estimated_health = float(np.mean(particles[:, 1]))
        
        capacity = node_data.get("capacity", 1.0)
        stress_score = min(estimated_load / capacity, 1.0) if capacity > 0 else 0.0
        failure_prob = self._calculate_failure_probability(stress_score, estimated_health)
        
        uncertainty = {
            "load": float(np.std(particles[:, 0])),
            "health": float(np.std(particles[:, 1]))
        }
        
        ci_load = (
            float(np.percentile(particles[:, 0], 2.5)),
            float(np.percentile(particles[:, 0], 97.5))
        )
        
        return StateEstimation(
            node_id=node_id,
            estimated_load=max(0, estimated_load),
            estimated_health=max(0, min(1, estimated_health)),
            stress_score=stress_score,
            failure_probability=failure_prob,
            uncertainty=uncertainty,
            confidence_interval=ci_load
        )
    
    def _calculate_failure_probability(self, stress_score: float, health: float) -> float:
        """Calculate failure probability from stress and health"""
        # Logistic function
        risk_score = stress_score * (1 - health)
        failure_prob = 1 / (1 + np.exp(-5 * (risk_score - 0.5)))
        return float(failure_prob)
    
    async def _get_node_data(self, node_id: str) -> Dict[str, Any]:
        """Fetch node data from knowledge graph"""
        try:
            response = await self.http_client.get(
                f"{self.knowledge_graph_url}/api/v1/graph/nodes/{node_id}"
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching node data: {e}")
        
        return {"capacity": 1.0, "current_load": 0.0, "health_status": 1.0}
    
    def _extract_measurements(
        self,
        sensor_data: List[Dict[str, Any]],
        node_id: str
    ) -> Optional[np.ndarray]:
        """Extract measurements for a specific node"""
        node_measurements = [
            d for d in sensor_data 
            if d.get("node_id") == node_id
        ]
        
        if not node_measurements:
            return None
        
        measurements = np.array([
            [d.get("load", 0.0), d.get("health", 1.0)]
            for d in node_measurements
        ])
        
        return measurements


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

engine: Optional[StateEstimationEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    engine = StateEstimationEngine(
        knowledge_graph_url="http://knowledge-graph:8002"
    )
    yield
    if engine:
        await engine.http_client.aclose()

app = FastAPI(
    title="STRATUM PROTOCOL - State Estimation Engine",
    description="Bayesian inference for infrastructure state estimation",
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
    return {"status": "healthy", "service": "state-estimation"}

@app.post("/api/v1/estimate/states", response_model=List[StateEstimation])
async def estimate_states(request: StateEstimationRequest):
    """Estimate infrastructure states"""
    if not engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    estimations = await engine.estimate_states(request)
    return estimations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
