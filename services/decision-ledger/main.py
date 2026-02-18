"""
STRATUM PROTOCOL - Decision Ledger Service
Cryptographically verifiable blockchain-style audit trail for decisions
"""
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import uuid4
import hashlib
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import asyncpg
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DecisionRecord(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid4()))
    decision_type: str
    parameters: Dict[str, Any]
    outcomes: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    authority: str
    previous_hash: str = ""
    current_hash: str = ""
    signature: str = ""

class VerificationResult(BaseModel):
    is_valid: bool
    chain_length: int
    broken_links: List[int]
    message: str

class DecisionLedgerService:
    """Blockchain-style immutable ledger"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.pool: Optional[asyncpg.Pool] = None
        logger.info("Decision Ledger initialized")
    
    async def start(self):
        """Initialize database connection"""
        self.pool = await asyncpg.create_pool(self.db_url, min_size=5, max_size=20)
        await self._init_schema()
        logger.info("Database connection established")
    
    async def stop(self):
        """Close database connection"""
        if self.pool:
            await self.pool.close()
    
    async def _init_schema(self):
        """Create ledger table"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS decision_ledger (
                    id SERIAL PRIMARY KEY,
                    decision_id VARCHAR(255) UNIQUE NOT NULL,
                    decision_type VARCHAR(100) NOT NULL,
                    parameters JSONB NOT NULL,
                    outcomes JSONB NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    authority VARCHAR(255) NOT NULL,
                    previous_hash VARCHAR(64) NOT NULL,
                    current_hash VARCHAR(64) UNIQUE NOT NULL,
                    signature VARCHAR(512) NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_decision_timestamp 
                ON decision_ledger(timestamp DESC)
            """)
    
    async def add_decision(self, record: DecisionRecord) -> DecisionRecord:
        """Add decision to ledger with cryptographic chaining"""
        
        # Get previous hash
        previous_hash = await self._get_latest_hash()
        record.previous_hash = previous_hash
        
        # Calculate current hash
        record.current_hash = self._calculate_hash(record)
        
        # Sign (simplified - in production use proper PKI)
        record.signature = self._sign_record(record)
        
        # Store in database
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO decision_ledger 
                (decision_id, decision_type, parameters, outcomes, timestamp, 
                 authority, previous_hash, current_hash, signature)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
                record.decision_id,
                record.decision_type,
                json.dumps(record.parameters),
                json.dumps(record.outcomes),
                record.timestamp,
                record.authority,
                record.previous_hash,
                record.current_hash,
                record.signature
            )
        
        logger.info(f"Decision {record.decision_id} added to ledger")
        return record
    
    async def verify_chain(self) -> VerificationResult:
        """Verify integrity of entire chain"""
        
        async with self.pool.acquire() as conn:
            records = await conn.fetch("""
                SELECT * FROM decision_ledger ORDER BY timestamp ASC
            """)
        
        if not records:
            return VerificationResult(
                is_valid=True,
                chain_length=0,
                broken_links=[],
                message="Empty chain"
            )
        
        broken_links = []
        previous_hash = ""
        
        for idx, record in enumerate(records):
            # Verify previous hash linkage
            if record['previous_hash'] != previous_hash:
                broken_links.append(idx)
            
            # Verify current hash
            calculated_hash = self._calculate_hash_from_db(record)
            if calculated_hash != record['current_hash']:
                broken_links.append(idx)
            
            previous_hash = record['current_hash']
        
        is_valid = len(broken_links) == 0
        
        return VerificationResult(
            is_valid=is_valid,
            chain_length=len(records),
            broken_links=broken_links,
            message="Chain is valid" if is_valid else f"Chain broken at {len(broken_links)} points"
        )
    
    async def get_decisions(
        self,
        decision_type: Optional[str] = None,
        authority: Optional[str] = None,
        limit: int = 100
    ) -> List[DecisionRecord]:
        """Query decisions"""
        
        query = "SELECT * FROM decision_ledger WHERE 1=1"
        params = []
        
        if decision_type:
            params.append(decision_type)
            query += f" AND decision_type = ${len(params)}"
        
        if authority:
            params.append(authority)
            query += f" AND authority = ${len(params)}"
        
        query += f" ORDER BY timestamp DESC LIMIT ${len(params) + 1}"
        params.append(limit)
        
        async with self.pool.acquire() as conn:
            records = await conn.fetch(query, *params)
        
        decisions = []
        for r in records:
            decisions.append(DecisionRecord(
                decision_id=r['decision_id'],
                decision_type=r['decision_type'],
                parameters=json.loads(r['parameters']),
                outcomes=json.loads(r['outcomes']),
                timestamp=r['timestamp'],
                authority=r['authority'],
                previous_hash=r['previous_hash'],
                current_hash=r['current_hash'],
                signature=r['signature']
            ))
        
        return decisions
    
    async def _get_latest_hash(self) -> str:
        """Get hash of most recent decision"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT current_hash FROM decision_ledger 
                ORDER BY timestamp DESC LIMIT 1
            """)
        
        return result or "0" * 64  # Genesis block
    
    def _calculate_hash(self, record: DecisionRecord) -> str:
        """Calculate SHA-256 hash of record"""
        data = f"{record.decision_id}{record.decision_type}" \
               f"{json.dumps(record.parameters)}{json.dumps(record.outcomes)}" \
               f"{record.timestamp.isoformat()}{record.authority}{record.previous_hash}"
        
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _calculate_hash_from_db(self, db_record) -> str:
        """Calculate hash from database record"""
        data = f"{db_record['decision_id']}{db_record['decision_type']}" \
               f"{db_record['parameters']}{db_record['outcomes']}" \
               f"{db_record['timestamp'].isoformat()}{db_record['authority']}" \
               f"{db_record['previous_hash']}"
        
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _sign_record(self, record: DecisionRecord) -> str:
        """Sign record (simplified RSA-style)"""
        # In production: use proper PKI with private key signing
        signature_data = f"{record.current_hash}{record.authority}"
        return hashlib.sha512(signature_data.encode()).hexdigest()

ledger: Optional[DecisionLedgerService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ledger
    ledger = DecisionLedgerService(
        db_url="postgresql://postgres:stratumdb123@postgres:5432/stratum_ledger"
    )
    await ledger.start()
    yield
    await ledger.stop()

app = FastAPI(
    title="STRATUM PROTOCOL - Decision Ledger",
    description="Cryptographic audit trail for sovereign decisions",
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
    return {"status": "healthy", "service": "decision-ledger"}

@app.post("/api/v1/ledger/decisions", response_model=DecisionRecord)
async def add_decision(record: DecisionRecord):
    """Add decision to immutable ledger"""
    if not ledger:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    result = await ledger.add_decision(record)
    return result

@app.get("/api/v1/ledger/verify", response_model=VerificationResult)
async def verify_chain():
    """Verify entire chain integrity"""
    if not ledger:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    result = await ledger.verify_chain()
    return result

@app.get("/api/v1/ledger/decisions", response_model=List[DecisionRecord])
async def get_decisions(
    decision_type: Optional[str] = None,
    authority: Optional[str] = None,
    limit: int = 100
):
    """Query decisions from ledger"""
    if not ledger:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    decisions = await ledger.get_decisions(decision_type, authority, limit)
    return decisions

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
