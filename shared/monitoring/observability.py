"""
Monitoring and Observability Utilities for STRATUM PROTOCOL
Provides Prometheus metrics, structured logging, and distributed tracing
"""

import os
import time
import logging
import json
from typing import Optional, Dict, Any
from functools import wraps
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST


# =============================================================================
# PROMETHEUS METRICS
# =============================================================================

class Metrics:
    """Centralized Prometheus metrics registry"""
    
    # Request metrics
    REQUEST_COUNT = Counter(
        'stratum_http_requests_total',
        'Total HTTP requests',
        ['service', 'method', 'endpoint', 'status']
    )
    
    REQUEST_DURATION = Histogram(
        'stratum_http_request_duration_seconds',
        'HTTP request duration',
        ['service', 'method', 'endpoint']
    )
    
    # Service health metrics
    SERVICE_UP = Gauge(
        'stratum_service_up',
        'Service availability',
        ['service']
    )
    
    SERVICE_INFO = Info(
        'stratum_service_info',
        'Service information',
        ['service']
    )
    
    # Business metrics
    DATA_INGESTION_COUNT = Counter(
        'stratum_data_ingestion_total',
        'Total data points ingested',
        ['source', 'type']
    )
    
    SIMULATION_COUNT = Counter(
        'stratum_simulations_total',
        'Total simulations run',
        ['type', 'status']
    )
    
    SIMULATION_DURATION = Histogram(
        'stratum_simulation_duration_seconds',
        'Simulation execution time',
        ['type']
    )
    
    GRAPH_NODE_COUNT = Gauge(
        'stratum_graph_nodes_total',
        'Total nodes in knowledge graph',
        ['type']
    )
    
    CRITICAL_NODES_COUNT = Gauge(
        'stratum_critical_nodes_total',
        'Number of critical infrastructure nodes',
        []
    )
    
    # Error metrics
    ERROR_COUNT = Counter(
        'stratum_errors_total',
        'Total errors',
        ['service', 'error_type']
    )
    
    @classmethod
    def expose_metrics(cls):
        """Generate Prometheus metrics in text format"""
        return generate_latest()
    
    @classmethod
    def get_content_type(cls):
        """Get Prometheus content type"""
        return CONTENT_TYPE_LATEST


def track_request(service_name: str):
    """
    Decorator to track HTTP request metrics
    
    Usage:
        @track_request("data-ingestion")
        @app.post("/api/v1/ingest")
        async def ingest_data():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                
                # Extract endpoint and method from function
                endpoint = func.__name__
                method = "POST"  # Can be extracted from route decorator
                
                Metrics.REQUEST_COUNT.labels(
                    service=service_name,
                    method=method,
                    endpoint=endpoint,
                    status=status
                ).inc()
                
                Metrics.REQUEST_DURATION.labels(
                    service=service_name,
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
        
        return wrapper
    return decorator


# =============================================================================
# STRUCTURED LOGGING
# =============================================================================

class StructuredLogger:
    """JSON structured logging for cloud-native environments"""
    
    def __init__(self, service_name: str, log_level: str = "INFO"):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(self._json_formatter())
        self.logger.addHandler(handler)
    
    def _json_formatter(self):
        """Create JSON log formatter"""
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": record.name,
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                # Add extra fields
                if hasattr(record, 'extra_fields'):
                    log_data.update(record.extra_fields)
                
                # Add exception info
                if record.exc_info:
                    log_data["exception"] = self.formatException(record.exc_info)
                
                return json.dumps(log_data)
        
        return JsonFormatter()
    
    def info(self, message: str, **extra_fields):
        """Log info message"""
        extra = {'extra_fields': extra_fields} if extra_fields else {}
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **extra_fields):
        """Log warning message"""
        extra = {'extra_fields': extra_fields} if extra_fields else {}
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, **extra_fields):
        """Log error message"""
        extra = {'extra_fields': extra_fields} if extra_fields else {}
        self.logger.error(message, extra=extra)
    
    def debug(self, message: str, **extra_fields):
        """Log debug message"""
        extra = {'extra_fields': extra_fields} if extra_fields else {}
        self.logger.debug(message, extra=extra)
    
    def critical(self, message: str, **extra_fields):
        """Log critical message"""
        extra = {'extra_fields': extra_fields} if extra_fields else {}
        self.logger.critical(message, extra=extra)


# =============================================================================
# DISTRIBUTED TRACING
# =============================================================================

class TracingContext:
    """Distributed tracing context for request correlation"""
    
    def __init__(
        self,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
        parent_span_id: Optional[str] = None
    ):
        self.trace_id = trace_id or self._generate_id()
        self.span_id = span_id or self._generate_id()
        self.parent_span_id = parent_span_id
        self.start_time = time.time()
        self.tags: Dict[str, Any] = {}
        self.logs: list = []
    
    @staticmethod
    def _generate_id() -> str:
        """Generate unique trace/span ID"""
        import uuid
        return uuid.uuid4().hex[:16]
    
    def add_tag(self, key: str, value: Any):
        """Add tag to span"""
        self.tags[key] = value
    
    def log_event(self, event: str, **fields):
        """Log event in span"""
        self.logs.append({
            "timestamp": time.time(),
            "event": event,
            **fields
        })
    
    def finish(self) -> Dict[str, Any]:
        """Finish span and return trace data"""
        duration = time.time() - self.start_time
        
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "duration_seconds": duration,
            "tags": self.tags,
            "logs": self.logs
        }
    
    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP headers for propagation"""
        return {
            "X-Trace-Id": self.trace_id,
            "X-Span-Id": self.span_id
        }
    
    @classmethod
    def from_headers(cls, headers: Dict[str, str]) -> 'TracingContext':
        """Create context from HTTP headers"""
        return cls(
            trace_id=headers.get("X-Trace-Id"),
            span_id=cls._generate_id(),
            parent_span_id=headers.get("X-Span-Id")
        )


def trace_function(operation_name: str):
    """
    Decorator to trace function execution
    
    Usage:
        @trace_function("compute_criticality")
        async def compute_scores():
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ctx = TracingContext()
            ctx.add_tag("operation", operation_name)
            ctx.add_tag("function", func.__name__)
            
            try:
                result = await func(*args, **kwargs)
                ctx.add_tag("status", "success")
                return result
            except Exception as e:
                ctx.add_tag("status", "error")
                ctx.add_tag("error", str(e))
                ctx.log_event("error", error_type=type(e).__name__)
                raise e
            finally:
                trace_data = ctx.finish()
                # Send to Jaeger/OpenTelemetry collector
                # For now, just log it
                print(f"TRACE: {json.dumps(trace_data)}")
        
        return wrapper
    return decorator


# =============================================================================
# HEALTH CHECK UTILITIES
# =============================================================================

class HealthChecker:
    """Service health check utilities"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.start_time = time.time()
        self.dependencies: Dict[str, bool] = {}
    
    def add_dependency(self, name: str, healthy: bool):
        """Register dependency health status"""
        self.dependencies[name] = healthy
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        all_healthy = all(self.dependencies.values())
        
        return {
            "service": self.service_name,
            "status": "healthy" if all_healthy else "degraded",
            "uptime_seconds": time.time() - self.start_time,
            "timestamp": datetime.utcnow().isoformat(),
            "dependencies": self.dependencies
        }
    
    def is_healthy(self) -> bool:
        """Check if service is healthy"""
        return all(self.dependencies.values())


# Example usage in FastAPI:
"""
from shared.monitoring.observability import Metrics, StructuredLogger, HealthChecker

# Setup
logger = StructuredLogger("data-ingestion")
health_checker = HealthChecker("data-ingestion")

# Endpoints
@app.get("/health")
async def health_check():
    return health_checker.get_health_status()

@app.get("/metrics")
async def metrics():
    return Response(
        content=Metrics.expose_metrics(),
        media_type=Metrics.get_content_type()
    )

# Usage
logger.info("Processing data", node_id="POWER_001", value=85.5)
Metrics.DATA_INGESTION_COUNT.labels(source="iot", type="power").inc()
"""
