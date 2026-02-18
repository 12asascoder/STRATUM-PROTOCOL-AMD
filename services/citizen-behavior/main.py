"""
STRATUM PROTOCOL - Citizen Behavior Simulation
Agent-based modeling for 100K+ autonomous citizen agents with evacuation planning
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4
from enum import Enum

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# DATA MODELS
# =============================================================================

class AgentState(str, Enum):
    NORMAL = "normal"
    ALERT = "alert"
    EVACUATING = "evacuating"
    SHELTERED = "sheltered"
    INJURED = "injured"

class CitizenAgent(BaseModel):
    agent_id: str = Field(default_factory=lambda: str(uuid4()))
    location: tuple[float, float]
    state: AgentState = AgentState.NORMAL
    vulnerability: float = Field(ge=0, le=1)  # 0=resilient, 1=vulnerable
    mobility: float = Field(ge=0, le=1)
    awareness: float = Field(ge=0, le=1)
    has_vehicle: bool = False
    household_size: int = 1

class EvacuationScenario(BaseModel):
    scenario_id: str = Field(default_factory=lambda: str(uuid4()))
    threat_location: tuple[float, float]
    threat_radius: float
    evacuation_zones: List[Dict[str, Any]]
    shelter_locations: List[tuple[float, float]]
    road_closures: List[str] = []
    num_agents: int = 10000
    simulation_duration: int = 3600  # seconds

class SimulationResult(BaseModel):
    scenario_id: str
    evacuated_count: int
    sheltered_count: int
    injured_count: int
    average_evacuation_time: float
    bottleneck_locations: List[tuple[float, float]]
    recommendations: List[str]
    agent_trajectories: List[List[tuple[float, float]]]

class CitizenBehaviorEngine:
    """Agent-based simulation engine"""
    
    def __init__(self):
        self.agents: Dict[str, CitizenAgent] = {}
        self.simulation_cache: Dict[str, SimulationResult] = {}
        logger.info("Citizen Behavior Engine initialized")
    
    async def run_evacuation_simulation(
        self,
        scenario: EvacuationScenario
    ) -> SimulationResult:
        """Run agent-based evacuation simulation"""
        
        # Initialize agents
        agents = self._initialize_agents(scenario)
        
        # Simulation loop
        timesteps = scenario.simulation_duration
        dt = 1.0  # seconds
        
        evacuated = 0
        sheltered = 0
        injured = 0
        evacuation_times = []
        trajectories = []
        bottlenecks = []
        
        for t in range(timesteps):
            # Update agent states
            for agent in agents:
                # Calculate danger
                distance_to_threat = self._calculate_distance(
                    agent.location,
                    scenario.threat_location
                )
                
                if distance_to_threat < scenario.threat_radius:
                    if agent.state == AgentState.NORMAL:
                        agent.state = AgentState.ALERT
                    
                    # Injury probability
                    injury_prob = (1 - distance_to_threat / scenario.threat_radius) * (1 - agent.vulnerability)
                    if np.random.random() < injury_prob * 0.001:
                        agent.state = AgentState.INJURED
                        injured += 1
                        continue
                
                # Decision making
                if agent.state == AgentState.ALERT:
                    # Start evacuating
                    agent.state = AgentState.EVACUATING
                
                if agent.state == AgentState.EVACUATING:
                    # Move towards nearest shelter
                    target_shelter = self._find_nearest_shelter(
                        agent.location,
                        scenario.shelter_locations
                    )
                    
                    # Move agent
                    speed = agent.mobility * (2.0 if agent.has_vehicle else 1.4)  # m/s
                    new_location = self._move_towards(
                        agent.location,
                        target_shelter,
                        speed * dt
                    )
                    agent.location = new_location
                    
                    # Check if reached shelter
                    if self._calculate_distance(agent.location, target_shelter) < 10:
                        agent.state = AgentState.SHELTERED
                        sheltered += 1
                        evacuation_times.append(t)
            
            # Detect bottlenecks (spatial clustering)
            if t % 60 == 0:  # Check every minute
                clusters = self._detect_clusters(
                    [a.location for a in agents if a.state == AgentState.EVACUATING]
                )
                bottlenecks.extend(clusters)
        
        # Calculate metrics
        evacuated = sum(1 for a in agents if a.state in [AgentState.EVACUATING, AgentState.SHELTERED])
        avg_evac_time = np.mean(evacuation_times) if evacuation_times else 0.0
        
        # Sample trajectories
        sample_agents = agents[:100]
        for agent in sample_agents:
            trajectories.append([agent.location])
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            agents,
            bottlenecks,
            scenario
        )
        
        result = SimulationResult(
            scenario_id=scenario.scenario_id,
            evacuated_count=evacuated,
            sheltered_count=sheltered,
            injured_count=injured,
            average_evacuation_time=float(avg_evac_time),
            bottleneck_locations=bottlenecks[:10],
            recommendations=recommendations,
            agent_trajectories=trajectories
        )
        
        self.simulation_cache[scenario.scenario_id] = result
        return result
    
    def _initialize_agents(self, scenario: EvacuationScenario) -> List[CitizenAgent]:
        """Initialize citizen agents"""
        agents = []
        
        for _ in range(scenario.num_agents):
            # Random location in city
            location = (
                np.random.uniform(-0.1, 0.1) + scenario.threat_location[0],
                np.random.uniform(-0.1, 0.1) + scenario.threat_location[1]
            )
            
            agent = CitizenAgent(
                location=location,
                vulnerability=np.random.beta(2, 5),  # Most people somewhat resilient
                mobility=np.random.beta(5, 2),  # Most people fairly mobile
                awareness=np.random.beta(4, 2),
                has_vehicle=np.random.random() < 0.65,
                household_size=int(np.random.exponential(1.5)) + 1
            )
            agents.append(agent)
        
        return agents
    
    def _calculate_distance(self, loc1: tuple, loc2: tuple) -> float:
        """Calculate Euclidean distance"""
        return np.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)
    
    def _find_nearest_shelter(
        self,
        location: tuple,
        shelters: List[tuple]
    ) -> tuple:
        """Find nearest shelter"""
        if not shelters:
            return (0.0, 0.0)
        
        distances = [self._calculate_distance(location, s) for s in shelters]
        return shelters[np.argmin(distances)]
    
    def _move_towards(
        self,
        current: tuple,
        target: tuple,
        distance: float
    ) -> tuple:
        """Move agent towards target"""
        dx = target[0] - current[0]
        dy = target[1] - current[1]
        current_dist = np.sqrt(dx**2 + dy**2)
        
        if current_dist < distance:
            return target
        
        ratio = distance / current_dist
        return (
            current[0] + dx * ratio,
            current[1] + dy * ratio
        )
    
    def _detect_clusters(self, locations: List[tuple]) -> List[tuple]:
        """Detect spatial clusters (bottlenecks)"""
        if len(locations) < 10:
            return []
        
        # Simple grid-based clustering
        grid = {}
        cell_size = 0.001  # ~100m
        
        for loc in locations:
            cell = (int(loc[0] / cell_size), int(loc[1] / cell_size))
            grid[cell] = grid.get(cell, 0) + 1
        
        # Find dense cells
        bottlenecks = []
        for cell, count in grid.items():
            if count > len(locations) * 0.05:  # 5% of agents in one cell
                bottlenecks.append((cell[0] * cell_size, cell[1] * cell_size))
        
        return bottlenecks
    
    def _generate_recommendations(
        self,
        agents: List[CitizenAgent],
        bottlenecks: List[tuple],
        scenario: EvacuationScenario
    ) -> List[str]:
        """Generate evacuation recommendations"""
        recommendations = []
        
        injured_count = sum(1 for a in agents if a.state == AgentState.INJURED)
        if injured_count > scenario.num_agents * 0.05:
            recommendations.append(
                f"CRITICAL: {injured_count} injuries detected. Deploy medical teams immediately."
            )
        
        if len(bottlenecks) > 5:
            recommendations.append(
                f"WARNING: {len(bottlenecks)} traffic bottlenecks detected. Consider alternate routes."
            )
        
        sheltered_ratio = sum(1 for a in agents if a.state == AgentState.SHELTERED) / len(agents)
        if sheltered_ratio < 0.5:
            recommendations.append(
                "Increase public awareness campaigns for evacuation procedures."
            )
        
        recommendations.append(
            f"Deploy emergency services to coordinates: {bottlenecks[:3]}"
        )
        
        return recommendations

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

engine: Optional[CitizenBehaviorEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    engine = CitizenBehaviorEngine()
    yield

app = FastAPI(
    title="STRATUM PROTOCOL - Citizen Behavior Simulation",
    description="Agent-based modeling for evacuation planning",
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
    return {"status": "healthy", "service": "citizen-behavior"}

@app.post("/api/v1/simulate/evacuation", response_model=SimulationResult)
async def simulate_evacuation(scenario: EvacuationScenario):
    """Run evacuation simulation"""
    if not engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    result = await engine.run_evacuation_simulation(scenario)
    return result

@app.get("/api/v1/simulations/{scenario_id}", response_model=SimulationResult)
async def get_simulation(scenario_id: str):
    """Get cached simulation result"""
    if not engine or scenario_id not in engine.simulation_cache:
        raise HTTPException(status_code=404, detail="Simulation not found")
    
    return engine.simulation_cache[scenario_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
