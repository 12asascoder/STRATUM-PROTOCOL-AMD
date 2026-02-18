"""
STRATUM PROTOCOL - Data Ingestion Service
Real-time streaming data ingestion with validation, normalization, and fault tolerance
"""
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import aiokafka
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import redis.asyncio as aioredis
import logging
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# METRICS
# =============================================================================
INGESTION_COUNTER = Counter('data_ingestion_total', 'Total data points ingested', ['source', 'type'])
INGESTION_LATENCY = Histogram('data_ingestion_latency_seconds', 'Data ingestion latency')
VALIDATION_ERRORS = Counter('data_validation_errors_total', 'Total validation errors', ['error_type'])
ACTIVE_STREAMS = Gauge('active_data_streams', 'Number of active data streams')
BUFFER_SIZE = Gauge('ingestion_buffer_size', 'Size of ingestion buffer')

# =============================================================================
# DATA MODELS
# =============================================================================

class DataSource(BaseModel):
    """Data source configuration"""
    source_id: str
    source_type: str  # iot, traffic, weather, social, economic
    name: str
    location: Optional[tuple[float, float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    sampling_rate_hz: Optional[float] = None
    is_active: bool = True


class IngestedDataPoint(BaseModel):
    """Raw ingested data point"""
    id: UUID = Field(default_factory=uuid4)
    source_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data_type: str
    payload: Dict[str, Any]
    quality_score: float = Field(default=1.0, ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


class ValidationRule(BaseModel):
    """Data validation rule"""
    field: str
    rule_type: str  # range, regex, enum, custom
    parameters: Dict[str, Any]
    severity: str = "error"  # error, warning


class StreamConfig(BaseModel):
    """Stream configuration"""
    stream_id: str
    source_id: str
    topic: str
    batch_size: int = 100
    flush_interval_seconds: float = 1.0
    validation_rules: List[ValidationRule] = Field(default_factory=list)


# =============================================================================
# DATA INGESTION SERVICE
# =============================================================================

class DataIngestionService:
    """Real-time data ingestion service with Kafka streaming"""
    
    def __init__(
        self,
        kafka_bootstrap_servers: str,
        redis_url: str,
        batch_size: int = 100,
        flush_interval: float = 1.0
    ):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.redis_url = redis_url
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        self.producer: Optional[AIOKafkaProducer] = None
        self.redis_client: Optional[aioredis.Redis] = None
        
        # In-memory buffers
        self.data_buffer: Dict[str, List[IngestedDataPoint]] = {}
        self.validation_cache: Dict[str, ValidationRule] = {}
        
        # Active streams tracking
        self.active_streams: Dict[str, StreamConfig] = {}
        
        logger.info("Data Ingestion Service initialized")
    
    async def start(self):
        """Start the service"""
        # Initialize Kafka producer
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            compression_type='gzip',
            acks='all',
            retries=3
        )
        await self.producer.start()
        logger.info("Kafka producer started")
        
        # Initialize Redis
        self.redis_client = await aioredis.from_url(self.redis_url)
        logger.info("Redis client connected")
        
        # Start background flush task
        asyncio.create_task(self._periodic_flush())
    
    async def stop(self):
        """Stop the service"""
        if self.producer:
            await self.producer.stop()
        if self.redis_client:
            await self.redis_client.close()
        logger.info("Data Ingestion Service stopped")
    
    async def ingest_data_point(
        self,
        data_point: IngestedDataPoint,
        stream_id: Optional[str] = None
    ) -> bool:
        """
        Ingest a single data point
        
        Args:
            data_point: Data point to ingest
            stream_id: Optional stream identifier
            
        Returns:
            True if ingestion successful
        """
        try:
            # Validate data point
            if stream_id and stream_id in self.active_streams:
                stream_config = self.active_streams[stream_id]
                is_valid, errors = await self._validate_data(
                    data_point,
                    stream_config.validation_rules
                )
                if not is_valid:
                    logger.warning(f"Validation failed for {data_point.id}: {errors}")
                    VALIDATION_ERRORS.labels(error_type='validation_failure').inc()
                    return False
            
            # Normalize data
            normalized_data = await self._normalize_data(data_point)
            
            # Buffer for batch processing
            source_id = data_point.source_id
            if source_id not in self.data_buffer:
                self.data_buffer[source_id] = []
            
            self.data_buffer[source_id].append(normalized_data)
            BUFFER_SIZE.set(sum(len(buf) for buf in self.data_buffer.values()))
            
            # Flush if batch size reached
            if len(self.data_buffer[source_id]) >= self.batch_size:
                await self._flush_buffer(source_id)
            
            # Update metrics
            INGESTION_COUNTER.labels(
                source=data_point.source_id,
                type=data_point.data_type
            ).inc()
            
            # Cache in Redis for real-time access
            await self._cache_data_point(normalized_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting data point: {e}")
            VALIDATION_ERRORS.labels(error_type='ingestion_error').inc()
            return False
    
    async def ingest_batch(
        self,
        data_points: List[IngestedDataPoint],
        stream_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ingest a batch of data points
        
        Returns:
            Statistics about ingestion
        """
        successful = 0
        failed = 0
        
        tasks = []
        for data_point in data_points:
            tasks.append(self.ingest_data_point(data_point, stream_id))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, bool) and result:
                successful += 1
            else:
                failed += 1
        
        return {
            "total": len(data_points),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(data_points) if data_points else 0
        }
    
    async def _validate_data(
        self,
        data_point: IngestedDataPoint,
        rules: List[ValidationRule]
    ) -> tuple[bool, List[str]]:
        """Validate data point against rules"""
        errors = []
        
        for rule in rules:
            field_value = data_point.payload.get(rule.field)
            
            if rule.rule_type == "range":
                min_val = rule.parameters.get("min")
                max_val = rule.parameters.get("max")
                if field_value is not None:
                    if min_val is not None and field_value < min_val:
                        errors.append(f"{rule.field} below minimum: {field_value} < {min_val}")
                    if max_val is not None and field_value > max_val:
                        errors.append(f"{rule.field} above maximum: {field_value} > {max_val}")
            
            elif rule.rule_type == "enum":
                allowed_values = rule.parameters.get("values", [])
                if field_value not in allowed_values:
                    errors.append(f"{rule.field} not in allowed values: {allowed_values}")
            
            elif rule.rule_type == "required":
                if field_value is None:
                    errors.append(f"{rule.field} is required but missing")
        
        return len(errors) == 0, errors
    
    async def _normalize_data(self, data_point: IngestedDataPoint) -> IngestedDataPoint:
        """Normalize data point (unit conversion, standardization)"""
        # Implement data normalization logic
        # For now, return as-is
        return data_point
    
    async def _flush_buffer(self, source_id: str):
        """Flush buffer to Kafka"""
        if source_id not in self.data_buffer or not self.data_buffer[source_id]:
            return
        
        buffer = self.data_buffer[source_id]
        topic = f"stratum.ingestion.{source_id}"
        
        try:
            # Send to Kafka
            for data_point in buffer:
                await self.producer.send(
                    topic,
                    value=data_point.dict()
                )
            
            logger.info(f"Flushed {len(buffer)} data points for {source_id}")
            self.data_buffer[source_id] = []
            BUFFER_SIZE.set(sum(len(buf) for buf in self.data_buffer.values()))
            
        except Exception as e:
            logger.error(f"Error flushing buffer: {e}")
    
    async def _periodic_flush(self):
        """Periodically flush all buffers"""
        while True:
            await asyncio.sleep(self.flush_interval)
            for source_id in list(self.data_buffer.keys()):
                await self._flush_buffer(source_id)
    
    async def _cache_data_point(self, data_point: IngestedDataPoint):
        """Cache data point in Redis for real-time access"""
        key = f"latest:{data_point.source_id}"
        await self.redis_client.setex(
            key,
            300,  # 5 minute TTL
            json.dumps(data_point.dict(), default=str)
        )
    
    async def register_stream(self, config: StreamConfig) -> bool:
        """Register a new data stream"""
        self.active_streams[config.stream_id] = config
        ACTIVE_STREAMS.set(len(self.active_streams))
        logger.info(f"Registered stream: {config.stream_id}")
        return True
    
    async def get_latest_data(self, source_id: str) -> Optional[IngestedDataPoint]:
        """Get latest data point for a source"""
        key = f"latest:{source_id}"
        data = await self.redis_client.get(key)
        if data:
            return IngestedDataPoint(**json.loads(data))
        return None


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

# Global service instance
service: Optional[DataIngestionService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    global service
    service = DataIngestionService(
        kafka_bootstrap_servers="kafka:29092",
        redis_url="redis://redis:6379/0"
    )
    await service.start()
    yield
    await service.stop()

app = FastAPI(
    title="STRATUM PROTOCOL - Data Ingestion Service",
    description="Real-time multi-source urban data ingestion",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "data-ingestion",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

@app.post("/api/v1/ingest/single")
async def ingest_single(data_point: IngestedDataPoint):
    """Ingest a single data point"""
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    success = await service.ingest_data_point(data_point)
    if success:
        return {"status": "success", "id": str(data_point.id)}
    else:
        raise HTTPException(status_code=400, detail="Ingestion failed")

@app.post("/api/v1/ingest/batch")
async def ingest_batch(data_points: List[IngestedDataPoint]):
    """Ingest a batch of data points"""
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    stats = await service.ingest_batch(data_points)
    return stats

@app.post("/api/v1/streams/register")
async def register_stream(config: StreamConfig):
    """Register a new data stream"""
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    success = await service.register_stream(config)
    return {"status": "registered", "stream_id": config.stream_id}

@app.get("/api/v1/sources/{source_id}/latest")
async def get_latest_data(source_id: str):
    """Get latest data point for a source"""
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    data = await service.get_latest_data(source_id)
    if data:
        return data
    else:
        raise HTTPException(status_code=404, detail="No data found")

@app.websocket("/ws/stream/{stream_id}")
async def websocket_stream(websocket: WebSocket, stream_id: str):
    """WebSocket endpoint for real-time data streaming"""
    await websocket.accept()
    logger.info(f"WebSocket connection established for stream: {stream_id}")
    
    try:
        while True:
            # In production, this would stream from Kafka
            # For now, send periodic updates
            await asyncio.sleep(1)
            await websocket.send_json({
                "stream_id": stream_id,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "active"
            })
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for stream: {stream_id}")

@app.get("/api/v1/streams")
async def list_streams():
    """List all active streams"""
    if not service:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {
        "streams": [
            {
                "stream_id": stream_id,
                "source_id": config.source_id,
                "topic": config.topic
            }
            for stream_id, config in service.active_streams.items()
        ],
        "count": len(service.active_streams)
    }

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
