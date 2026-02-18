"""
STRATUM PROTOCOL - Shared Data Models
Core domain models used across all microservices
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from uuid import UUID, uuid4


# =============================================================================
# ENUMS
# =============================================================================

class InfrastructureType(str, Enum):
    """Types of infrastructure assets"""
    POWER_GRID = "power_grid"
    WATER_SUPPLY = "water_supply"
    TRANSPORTATION = "transportation"
    TELECOM = "telecom"
    EMERGENCY_SERVICES = "emergency_services"
    HEALTHCARE = "healthcare"
    FINANCIAL = "financial"
    GOVERNMENT = "government"


class EventSeverity(str, Enum):
    """Severity levels for events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    CATASTROPHIC = "catastrophic"


class SimulationType(str, Enum):
    """Types of simulations"""
    CASCADING_FAILURE = "cascading_failure"
    CITIZEN_BEHAVIOR = "citizen_behavior"
    POLICY_OPTIMIZATION = "policy_optimization"
    ECONOMIC_IMPACT = "economic_impact"
    LONG_TERM_EVOLUTION = "long_term_evolution"


class DecisionStatus(str, Enum):
    """Status of decisions in the ledger"""
    PROPOSED = "proposed"
    SIMULATED = "simulated"
    APPROVED = "approved"
    EXECUTED = "executed"
    VALIDATED = "validated"
    REJECTED = "rejected"


class ThreatType(str, Enum):
    """Types of threats"""
    NATURAL_DISASTER = "natural_disaster"
    CYBERATTACK = "cyberattack"
    PHYSICAL_ATTACK = "physical_attack"
    SYSTEM_FAILURE = "system_failure"
    ECONOMIC_SHOCK = "economic_shock"
    PANDEMIC = "pandemic"


# =============================================================================
# CORE ENTITIES
# =============================================================================

class InfrastructureNode(BaseModel):
    """Represents a node in the urban knowledge graph"""
    id: UUID = Field(default_factory=uuid4)
    node_id: str = Field(..., description="Unique node identifier")
    name: str
    type: InfrastructureType
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    capacity: float = Field(..., gt=0)
    current_load: float = Field(default=0.0, ge=0)
    criticality_score: float = Field(default=0.5, ge=0, le=1)
    health_status: float = Field(default=1.0, ge=0, le=1)
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator('current_load')
    def validate_load(cls, v, values):
        if 'capacity' in values and v > values['capacity']:
            raise ValueError(f"Current load {v} exceeds capacity {values['capacity']}")
        return v

    @property
    def load_percentage(self) -> float:
        """Calculate load as percentage of capacity"""
        return (self.current_load / self.capacity) * 100 if self.capacity > 0 else 0

    @property
    def is_stressed(self) -> bool:
        """Check if node is under stress (>80% capacity)"""
        return self.load_percentage > 80


class InfrastructureDependency(BaseModel):
    """Represents a dependency edge in the knowledge graph"""
    id: UUID = Field(default_factory=uuid4)
    source_node_id: str
    target_node_id: str
    dependency_type: str
    strength: float = Field(..., ge=0, le=1, description="Dependency strength")
    bidirectional: bool = False
    failure_propagation_probability: float = Field(default=0.5, ge=0, le=1)
    latency_ms: Optional[float] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class UrbanEvent(BaseModel):
    """Represents an event affecting the urban system"""
    id: UUID = Field(default_factory=uuid4)
    event_type: str
    severity: EventSeverity
    description: str
    affected_nodes: List[str] = Field(default_factory=list)
    impact_radius_km: Optional[float] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    start_time: datetime
    end_time: Optional[datetime] = None
    probability: float = Field(default=1.0, ge=0, le=1)
    properties: Dict[str, Any] = Field(default_factory=dict)


class SensorData(BaseModel):
    """Real-time sensor telemetry data"""
    id: UUID = Field(default_factory=uuid4)
    sensor_id: str
    node_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metric_name: str
    value: float
    unit: str
    quality_score: float = Field(default=1.0, ge=0, le=1)
    anomaly_score: Optional[float] = Field(None, ge=0, le=1)
    properties: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# SIMULATION MODELS
# =============================================================================

class SimulationRequest(BaseModel):
    """Request for running a simulation"""
    id: UUID = Field(default_factory=uuid4)
    simulation_type: SimulationType
    scenario_name: str
    description: Optional[str] = None
    initial_conditions: Dict[str, Any]
    event_triggers: List[UrbanEvent] = Field(default_factory=list)
    simulation_horizon_hours: int = Field(default=24, gt=0)
    monte_carlo_runs: int = Field(default=1000, gt=0)
    confidence_level: float = Field(default=0.95, ge=0, le=1)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)


class SimulationResult(BaseModel):
    """Results from a simulation run"""
    id: UUID = Field(default_factory=uuid4)
    simulation_request_id: UUID
    status: str = Field(default="running")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    # Results
    affected_nodes: List[str] = Field(default_factory=list)
    cascade_depth: int = Field(default=0)
    total_impact_score: float = Field(default=0.0)
    economic_impact_usd: Optional[float] = None
    affected_population: Optional[int] = None
    
    # Statistical results
    mean_outcome: Optional[float] = None
    std_deviation: Optional[float] = None
    confidence_intervals: Optional[Dict[str, List[float]]] = None
    percentiles: Optional[Dict[str, float]] = None
    
    # Detailed results
    time_series_results: Optional[List[Dict[str, Any]]] = None
    node_impact_scores: Optional[Dict[str, float]] = None
    recommendations: List[str] = Field(default_factory=list)
    
    properties: Dict[str, Any] = Field(default_factory=dict)


class CascadingFailureResult(BaseModel):
    """Specific results for cascading failure simulation"""
    simulation_result_id: UUID
    failure_sequence: List[Dict[str, Any]] = Field(default_factory=list)
    failure_tree: Optional[Dict[str, Any]] = None
    critical_paths: List[List[str]] = Field(default_factory=list)
    bottleneck_nodes: List[str] = Field(default_factory=list)
    mean_time_to_cascade_minutes: Optional[float] = None
    cascade_probability: float = Field(..., ge=0, le=1)


# =============================================================================
# POLICY & DECISION MODELS
# =============================================================================

class PolicyAction(BaseModel):
    """Represents a policy action that can be taken"""
    id: UUID = Field(default_factory=uuid4)
    action_type: str
    target_nodes: List[str]
    description: str
    estimated_cost_usd: float = Field(..., ge=0)
    implementation_time_days: float = Field(..., gt=0)
    expected_impact: Dict[str, float] = Field(default_factory=dict)
    constraints: List[str] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)


class PolicyOptimizationRequest(BaseModel):
    """Request for policy optimization"""
    id: UUID = Field(default_factory=uuid4)
    objective: str
    candidate_actions: List[PolicyAction]
    constraints: Dict[str, Any] = Field(default_factory=dict)
    optimization_horizon_years: int = Field(default=5, gt=0)
    budget_usd: float = Field(..., ge=0)
    risk_tolerance: float = Field(default=0.5, ge=0, le=1)
    objectives_weights: Dict[str, float] = Field(default_factory=dict)
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)


class PolicyOptimizationResult(BaseModel):
    """Results from policy optimization"""
    id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    optimal_actions: List[PolicyAction]
    pareto_frontier: Optional[List[Dict[str, Any]]] = None
    expected_outcomes: Dict[str, float]
    risk_metrics: Dict[str, float]
    cost_benefit_ratio: float
    implementation_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    sensitivity_analysis: Optional[Dict[str, Any]] = None
    computed_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# DECISION LEDGER MODELS
# =============================================================================

class DecisionRecord(BaseModel):
    """Immutable decision record for the ledger"""
    id: UUID = Field(default_factory=uuid4)
    decision_id: str = Field(..., description="Unique decision identifier")
    decision_type: str
    status: DecisionStatus
    
    # Decision context
    description: str
    rationale: str
    proposed_by: str
    approved_by: Optional[str] = None
    
    # AI predictions
    ai_recommendation: Optional[str] = None
    ai_confidence: Optional[float] = Field(None, ge=0, le=1)
    ai_model_version: Optional[str] = None
    simulation_results_id: Optional[UUID] = None
    
    # Execution
    executed_at: Optional[datetime] = None
    execution_status: Optional[str] = None
    
    # Validation
    actual_outcome: Optional[Dict[str, Any]] = None
    outcome_measured_at: Optional[datetime] = None
    prediction_accuracy: Optional[float] = None
    
    # Cryptographic verification
    previous_hash: Optional[str] = None
    current_hash: str
    signature: str
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# CITIZEN BEHAVIOR MODELS
# =============================================================================

class CitizenAgent(BaseModel):
    """Agent-based model of citizen behavior"""
    id: UUID = Field(default_factory=uuid4)
    agent_id: str
    demographic_profile: Dict[str, Any]
    current_location: tuple[float, float]  # (lat, lon)
    home_location: tuple[float, float]
    work_location: Optional[tuple[float, float]] = None
    
    # Behavioral parameters
    risk_aversion: float = Field(default=0.5, ge=0, le=1)
    compliance_probability: float = Field(default=0.7, ge=0, le=1)
    mobility_capability: float = Field(default=1.0, ge=0, le=1)
    information_awareness: float = Field(default=0.5, ge=0, le=1)
    
    # State
    current_state: str = Field(default="normal")
    stress_level: float = Field(default=0.0, ge=0, le=1)
    needs: Dict[str, float] = Field(default_factory=dict)


class EvacuationScenario(BaseModel):
    """Evacuation simulation scenario"""
    id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    affected_zone: Dict[str, Any]
    safe_zones: List[Dict[str, Any]]
    population_size: int = Field(..., gt=0)
    evacuation_order_time: datetime
    simulation_duration_hours: int = Field(default=24, gt=0)
    transportation_capacity: Dict[str, int] = Field(default_factory=dict)


# =============================================================================
# ECONOMIC MODELS
# =============================================================================

class EconomicImpactAssessment(BaseModel):
    """Economic impact assessment"""
    id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    assessment_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Direct impacts
    infrastructure_damage_usd: float = Field(default=0.0, ge=0)
    business_interruption_usd: float = Field(default=0.0, ge=0)
    emergency_response_cost_usd: float = Field(default=0.0, ge=0)
    
    # Indirect impacts
    gdp_impact_usd: float = Field(default=0.0)
    employment_impact_jobs: int = Field(default=0)
    supply_chain_disruption_usd: float = Field(default=0.0, ge=0)
    
    # Financial metrics
    insurance_claims_usd: float = Field(default=0.0, ge=0)
    government_aid_usd: float = Field(default=0.0, ge=0)
    recovery_cost_usd: float = Field(default=0.0, ge=0)
    recovery_time_days: Optional[float] = None
    
    # Risk metrics
    value_at_risk_usd: Optional[float] = None
    expected_loss_usd: Optional[float] = None
    confidence_level: float = Field(default=0.95, ge=0, le=1)


# =============================================================================
# THREAT MODELS
# =============================================================================

class ThreatScenario(BaseModel):
    """Cyber-physical threat scenario"""
    id: UUID = Field(default_factory=uuid4)
    threat_type: ThreatType
    name: str
    description: str
    severity: EventSeverity
    
    # Attack vector
    entry_points: List[str] = Field(default_factory=list)
    target_nodes: List[str] = Field(default_factory=list)
    attack_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Characteristics
    sophistication_level: float = Field(default=0.5, ge=0, le=1)
    detection_difficulty: float = Field(default=0.5, ge=0, le=1)
    mitigation_difficulty: float = Field(default=0.5, ge=0, le=1)
    
    # Impact
    estimated_probability: float = Field(..., ge=0, le=1)
    potential_impact_score: float = Field(..., ge=0, le=1)


# =============================================================================
# FEDERATED LEARNING MODELS
# =============================================================================

class FederatedModelUpdate(BaseModel):
    """Model update from federated learning"""
    id: UUID = Field(default_factory=uuid4)
    city_id: str
    model_name: str
    model_version: str
    update_round: int
    
    # Privacy-preserving parameters
    gradient_updates: Optional[Dict[str, Any]] = None
    aggregated_metrics: Dict[str, float]
    differential_privacy_epsilon: float
    
    # Metadata
    training_samples: int
    training_duration_seconds: float
    validation_accuracy: float
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# ORCHESTRATION MODELS
# =============================================================================

class OrchestrationAction(BaseModel):
    """Autonomous orchestration action"""
    id: UUID = Field(default_factory=uuid4)
    action_type: str
    target_system: str
    target_nodes: List[str]
    
    # Action details
    command: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    estimated_impact: Dict[str, float]
    
    # Safety
    requires_approval: bool = Field(default=True)
    approved_by: Optional[str] = None
    safety_constraints: List[str] = Field(default_factory=list)
    
    # Execution
    scheduled_time: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    execution_result: Optional[Dict[str, Any]] = None
    rollback_available: bool = Field(default=False)
    
    # Audit
    created_by: str = "system"
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate Haversine distance between two coordinates"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # Earth's radius in km
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c
