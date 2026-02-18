"""
STRATUM PROTOCOL - Policy Simulation & Optimization Engine
Multi-objective policy optimization with Pareto frontier analysis
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
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolicyType(str, Enum):
    INFRASTRUCTURE = "infrastructure"
    TRAFFIC = "traffic"
    EMERGENCY = "emergency"
    ECONOMIC = "economic"

class PolicyAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid4()))
    policy_type: PolicyType
    parameters: Dict[str, Any]
    cost: float
    implementation_time: int  # days

class PolicyOptimizationRequest(BaseModel):
    objectives: List[str]  # ["minimize_casualties", "minimize_cost", "maximize_resilience"]
    constraints: Dict[str, float]
    candidate_actions: List[PolicyAction]
    simulation_scenarios: List[str]

class PolicyResult(BaseModel):
    action_id: str
    fitness_scores: Dict[str, float]
    expected_outcomes: Dict[str, Any]
    pareto_rank: int

class PolicyOptimizationEngine:
    """NSGA-II Multi-objective optimization"""
    
    def __init__(self, cascade_url: str):
        self.cascade_url = cascade_url
        self.http_client = httpx.AsyncClient(timeout=60.0)
        logger.info("Policy Optimization Engine initialized")
    
    async def optimize_policies(
        self,
        request: PolicyOptimizationRequest
    ) -> List[PolicyResult]:
        """Run multi-objective optimization"""
        
        population = request.candidate_actions
        num_generations = 50
        
        for gen in range(num_generations):
            # Evaluate fitness
            fitness_scores = await self._evaluate_population(population, request)
            
            # Pareto ranking
            pareto_fronts = self._fast_non_dominated_sort(fitness_scores, request.objectives)
            
            # Selection
            selected = self._selection(population, pareto_fronts, len(population) // 2)
            
            # Crossover & Mutation
            offspring = self._generate_offspring(selected)
            
            population = selected + offspring
        
        # Final evaluation
        final_fitness = await self._evaluate_population(population, request)
        pareto_fronts = self._fast_non_dominated_sort(final_fitness, request.objectives)
        
        results = []
        for i, action in enumerate(population):
            rank = next((r for r, front in enumerate(pareto_fronts) if i in front), 99)
            results.append(PolicyResult(
                action_id=action.action_id,
                fitness_scores=final_fitness[i],
                expected_outcomes={"estimated_impact": "high"},
                pareto_rank=rank
            ))
        
        return sorted(results, key=lambda x: x.pareto_rank)
    
    async def _evaluate_population(
        self,
        population: List[PolicyAction],
        request: PolicyOptimizationRequest
    ) -> List[Dict[str, float]]:
        """Evaluate fitness for all policies"""
        
        fitness_scores = []
        
        for action in population:
            scores = {}
            
            # Simulate impact (call cascade simulation)
            try:
                impact = await self._simulate_policy_impact(action)
                scores["casualties"] = impact.get("casualties", 0)
                scores["cost"] = action.cost
                scores["resilience"] = impact.get("resilience_improvement", 0)
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                scores = {"casualties": 1000, "cost": action.cost, "resilience": 0}
            
            fitness_scores.append(scores)
        
        return fitness_scores
    
    async def _simulate_policy_impact(self, action: PolicyAction) -> Dict[str, Any]:
        """Simulate policy impact via cascade engine"""
        # Simplified - would call cascade simulation
        return {
            "casualties": max(0, np.random.normal(100, 30)),
            "resilience_improvement": np.random.uniform(0, 1)
        }
    
    def _fast_non_dominated_sort(
        self,
        fitness_scores: List[Dict[str, float]],
        objectives: List[str]
    ) -> List[List[int]]:
        """NSGA-II fast non-dominated sorting"""
        
        n = len(fitness_scores)
        domination_count = [0] * n
        dominated_solutions = [[] for _ in range(n)]
        fronts = [[]]
        
        for i in range(n):
            for j in range(i + 1, n):
                if self._dominates(fitness_scores[i], fitness_scores[j], objectives):
                    dominated_solutions[i].append(j)
                    domination_count[j] += 1
                elif self._dominates(fitness_scores[j], fitness_scores[i], objectives):
                    dominated_solutions[j].append(i)
                    domination_count[i] += 1
            
            if domination_count[i] == 0:
                fronts[0].append(i)
        
        current_front = 0
        while fronts[current_front]:
            next_front = []
            for i in fronts[current_front]:
                for j in dominated_solutions[i]:
                    domination_count[j] -= 1
                    if domination_count[j] == 0:
                        next_front.append(j)
            current_front += 1
            if next_front:
                fronts.append(next_front)
        
        return fronts
    
    def _dominates(
        self,
        fitness1: Dict[str, float],
        fitness2: Dict[str, float],
        objectives: List[str]
    ) -> bool:
        """Check if fitness1 dominates fitness2"""
        
        better_in_any = False
        
        for obj in objectives:
            val1 = fitness1.get(obj.replace("minimize_", "").replace("maximize_", ""), 0)
            val2 = fitness2.get(obj.replace("minimize_", "").replace("maximize_", ""), 0)
            
            if "minimize" in obj:
                if val1 > val2:
                    return False
                if val1 < val2:
                    better_in_any = True
            else:  # maximize
                if val1 < val2:
                    return False
                if val1 > val2:
                    better_in_any = True
        
        return better_in_any
    
    def _selection(
        self,
        population: List[PolicyAction],
        fronts: List[List[int]],
        num_select: int
    ) -> List[PolicyAction]:
        """Tournament selection"""
        selected = []
        
        for front in fronts:
            if len(selected) + len(front) <= num_select:
                selected.extend([population[i] for i in front])
            else:
                remaining = num_select - len(selected)
                selected.extend([population[i] for i in front[:remaining]])
                break
        
        return selected
    
    def _generate_offspring(self, parents: List[PolicyAction]) -> List[PolicyAction]:
        """Generate offspring via crossover and mutation"""
        offspring = []
        
        for i in range(0, len(parents) - 1, 2):
            child1, child2 = self._crossover(parents[i], parents[i + 1])
            child1 = self._mutate(child1)
            child2 = self._mutate(child2)
            offspring.extend([child1, child2])
        
        return offspring
    
    def _crossover(self, parent1: PolicyAction, parent2: PolicyAction) -> tuple:
        """Uniform crossover"""
        child1_params = {}
        child2_params = {}
        
        for key in parent1.parameters:
            if np.random.random() < 0.5:
                child1_params[key] = parent1.parameters[key]
                child2_params[key] = parent2.parameters.get(key, parent1.parameters[key])
            else:
                child1_params[key] = parent2.parameters.get(key, parent1.parameters[key])
                child2_params[key] = parent1.parameters[key]
        
        child1 = PolicyAction(
            policy_type=parent1.policy_type,
            parameters=child1_params,
            cost=(parent1.cost + parent2.cost) / 2,
            implementation_time=parent1.implementation_time
        )
        
        child2 = PolicyAction(
            policy_type=parent2.policy_type,
            parameters=child2_params,
            cost=(parent1.cost + parent2.cost) / 2,
            implementation_time=parent2.implementation_time
        )
        
        return child1, child2
    
    def _mutate(self, action: PolicyAction) -> PolicyAction:
        """Gaussian mutation"""
        if np.random.random() < 0.1:  # 10% mutation rate
            mutated_params = {}
            for key, value in action.parameters.items():
                if isinstance(value, (int, float)):
                    mutated_params[key] = value * (1 + np.random.normal(0, 0.1))
                else:
                    mutated_params[key] = value
            
            return PolicyAction(
                policy_type=action.policy_type,
                parameters=mutated_params,
                cost=action.cost * (1 + np.random.normal(0, 0.05)),
                implementation_time=action.implementation_time
            )
        
        return action

engine: Optional[PolicyOptimizationEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    engine = PolicyOptimizationEngine(cascade_url="http://cascading-failure:8005")
    yield
    if engine:
        await engine.http_client.aclose()

app = FastAPI(
    title="STRATUM PROTOCOL - Policy Optimization",
    description="Multi-objective policy optimization",
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
    return {"status": "healthy", "service": "policy-optimization"}

@app.post("/api/v1/optimize/policies", response_model=List[PolicyResult])
async def optimize_policies(request: PolicyOptimizationRequest):
    """Run multi-objective policy optimization"""
    if not engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    results = await engine.optimize_policies(request)
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
