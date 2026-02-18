"""
STRATUM PROTOCOL - Economic Intelligence Engine
GDP impact modeling, ROI analysis, and risk assessment
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import numpy as np
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EconomicImpactRequest(BaseModel):
    scenario_id: str
    affected_sectors: List[str]
    duration_days: int
    infrastructure_damage: float  # 0-1
    population_affected: int

class EconomicMetrics(BaseModel):
    gdp_impact: float  # billions
    job_losses: int
    business_disruption_cost: float
    recovery_cost: float
    total_economic_loss: float
    roi_of_prevention: float
    var_95: float  # Value at Risk
    cvar_95: float  # Conditional VaR

class EconomicEngine:
    """Economic impact modeling"""
    
    def __init__(self):
        self.sector_weights = {
            "manufacturing": 0.12,
            "services": 0.55,
            "retail": 0.15,
            "tech": 0.18
        }
        logger.info("Economic Engine initialized")
    
    async def calculate_impact(
        self,
        request: EconomicImpactRequest
    ) -> EconomicMetrics:
        """Calculate economic impact"""
        
        # GDP impact modeling
        gdp_loss = self._calculate_gdp_impact(
            request.affected_sectors,
            request.duration_days,
            request.infrastructure_damage
        )
        
        # Job losses
        job_losses = self._estimate_job_losses(
            request.population_affected,
            request.duration_days
        )
        
        # Business disruption
        disruption_cost = self._calculate_business_disruption(
            request.affected_sectors,
            request.duration_days
        )
        
        # Recovery cost
        recovery_cost = self._estimate_recovery_cost(
            request.infrastructure_damage,
            gdp_loss
        )
        
        # Risk metrics
        var_95 = self._calculate_var(gdp_loss, 0.95)
        cvar_95 = self._calculate_cvar(gdp_loss, 0.95)
        
        # ROI of prevention
        prevention_cost = recovery_cost * 0.2  # Assume prevention costs 20%
        roi = (recovery_cost - prevention_cost) / prevention_cost
        
        return EconomicMetrics(
            gdp_impact=gdp_loss,
            job_losses=job_losses,
            business_disruption_cost=disruption_cost,
            recovery_cost=recovery_cost,
            total_economic_loss=gdp_loss + disruption_cost + recovery_cost,
            roi_of_prevention=roi,
            var_95=var_95,
            cvar_95=cvar_95
        )
    
    def _calculate_gdp_impact(
        self,
        sectors: List[str],
        duration: int,
        damage: float
    ) -> float:
        """Calculate GDP impact in billions"""
        
        daily_gdp = 50.0  # billion per day (example national GDP)
        
        sector_impact = sum(
            self.sector_weights.get(s, 0.1) for s in sectors
        )
        
        gdp_loss = daily_gdp * sector_impact * (duration / 365) * damage
        
        return gdp_loss
    
    def _estimate_job_losses(self, population: int, duration: int) -> int:
        """Estimate temporary job losses"""
        
        labor_force_ratio = 0.5
        unemployment_rate = min(0.3, duration / 100)
        
        job_losses = int(population * labor_force_ratio * unemployment_rate)
        
        return job_losses
    
    def _calculate_business_disruption(
        self,
        sectors: List[str],
        duration: int
    ) -> float:
        """Calculate business disruption cost"""
        
        daily_disruption = 1.5  # billion per day per sector
        
        total_disruption = len(sectors) * daily_disruption * duration
        
        return total_disruption
    
    def _estimate_recovery_cost(self, damage: float, gdp_loss: float) -> float:
        """Estimate infrastructure recovery cost"""
        
        base_recovery = damage * 100  # billion
        multiplier = 1 + (gdp_loss / 100)  # Larger losses = higher recovery costs
        
        return base_recovery * multiplier
    
    def _calculate_var(self, expected_loss: float, confidence: float) -> float:
        """Calculate Value at Risk"""
        
        # Assume normal distribution
        std_dev = expected_loss * 0.3
        z_score = 1.645 if confidence == 0.95 else 2.326
        
        var = expected_loss + z_score * std_dev
        
        return var
    
    def _calculate_cvar(self, expected_loss: float, confidence: float) -> float:
        """Calculate Conditional VaR (Expected Shortfall)"""
        
        var = self._calculate_var(expected_loss, confidence)
        
        # CVaR is typically 10-30% higher than VaR
        cvar = var * 1.2
        
        return cvar

engine: Optional[EconomicEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    engine = EconomicEngine()
    yield

app = FastAPI(
    title="STRATUM PROTOCOL - Economic Intelligence",
    description="Economic impact modeling and risk assessment",
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
    return {"status": "healthy", "service": "economic-intelligence"}

@app.post("/api/v1/calculate/impact", response_model=EconomicMetrics)
async def calculate_impact(request: EconomicImpactRequest):
    """Calculate economic impact"""
    if not engine:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    metrics = await engine.calculate_impact(request)
    return metrics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
