# utils/monitoring.py
import time
import asyncio
from functools import wraps
from typing import Callable, Dict, Any
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from threading import Lock

# Prometheus metrics
query_counter = Counter('mseis_queries_total', 'Total queries processed', ['agent', 'status'])
query_duration = Histogram('mseis_query_duration_seconds', 'Query processing time', ['agent'])
active_queries = Gauge('mseis_active_queries', 'Currently active queries', ['agent'])
cache_hits = Counter('mseis_cache_hits_total', 'Cache hits', ['namespace'])
cache_misses = Counter('mseis_cache_misses_total', 'Cache misses', ['namespace'])

# Thread-safe metrics storage
_metrics_lock = Lock()
_agent_metrics: Dict[str, Dict[str, Any]] = {}

def monitor_performance(agent_name: str, operation: str = "process"):
    """Decorator to monitor agent performance"""
    
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Increment active queries
            active_queries.labels(agent=agent_name).inc()
            
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                # Record metrics
                duration = time.time() - start_time
                query_counter.labels(agent=agent_name, status=status).inc()
                query_duration.labels(agent=agent_name).observe(duration)
                active_queries.labels(agent=agent_name).dec()
                
                # Update internal metrics
                with _metrics_lock:
                    if agent_name not in _agent_metrics:
                        _agent_metrics[agent_name] = {
                            "total_queries": 0,
                            "successful_queries": 0,
                            "failed_queries": 0,
                            "avg_response_time": 0.0,
                            "total_response_time": 0.0
                        }
                    
                    metrics = _agent_metrics[agent_name]
                    metrics["total_queries"] += 1
                    metrics["total_response_time"] += duration
                    
                    if status == "success":
                        metrics["successful_queries"] += 1
                    else:
                        metrics["failed_queries"] += 1
                        
                    metrics["avg_response_time"] = (
                        metrics["total_response_time"] / metrics["total_queries"]
                    )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Similar logic for synchronous functions
            active_queries.labels(agent=agent_name).inc()
            
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                query_counter.labels(agent=agent_name, status=status).inc()
                query_duration.labels(agent=agent_name).observe(duration)
                active_queries.labels(agent=agent_name).dec()
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator

def start_metrics_server(port: int = 8000):
    """Start Prometheus metrics server"""
    try:
        start_http_server(port)
        print(f"Metrics server started on port {port}")
    except Exception as e:
        print(f"Failed to start metrics server: {e}")

def get_agent_metrics(agent_name: str) -> Dict[str, Any]:
    """Get metrics for a specific agent"""
    with _metrics_lock:
        return _agent_metrics.get(agent_name, {})

def get_all_metrics() -> Dict[str, Any]:
    """Get all agent metrics"""
    with _metrics_lock:
        return _agent_metrics.copy() 