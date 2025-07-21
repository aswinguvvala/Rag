# utils/monitoring.py
import time
import asyncio
from functools import wraps
from typing import Dict, Any, Callable, Optional
from datetime import datetime
import threading
from collections import defaultdict, deque

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Global metrics storage
_metrics = defaultdict(lambda: {
    'call_count': 0,
    'total_time': 0.0,
    'avg_time': 0.0,
    'min_time': float('inf'),
    'max_time': 0.0,
    'recent_calls': deque(maxlen=100),
    'errors': 0,
    'last_called': None
})

_metrics_lock = threading.Lock()

def monitor_performance(component: str, operation: str):
    """Decorator to monitor performance of functions/methods"""
    
    def decorator(func: Callable) -> Callable:
        metric_key = f"{component}.{operation}"
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    _update_metrics(metric_key, execution_time, success=True)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    _update_metrics(metric_key, execution_time, success=False)
                    logger.error(f"Error in {metric_key}: {str(e)}")
                    raise
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    _update_metrics(metric_key, execution_time, success=True)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    _update_metrics(metric_key, execution_time, success=False)
                    logger.error(f"Error in {metric_key}: {str(e)}")
                    raise
            return sync_wrapper
            
    return decorator

def _update_metrics(metric_key: str, execution_time: float, success: bool = True):
    """Update metrics for a given operation"""
    with _metrics_lock:
        metrics = _metrics[metric_key]
        
        metrics['call_count'] += 1
        metrics['total_time'] += execution_time
        metrics['avg_time'] = metrics['total_time'] / metrics['call_count']
        metrics['min_time'] = min(metrics['min_time'], execution_time)
        metrics['max_time'] = max(metrics['max_time'], execution_time)
        metrics['last_called'] = datetime.now().isoformat()
        
        if not success:
            metrics['errors'] += 1
            
        # Store recent call info
        metrics['recent_calls'].append({
            'timestamp': datetime.now().isoformat(),
            'execution_time': execution_time,
            'success': success
        })

def get_metrics(component: Optional[str] = None) -> Dict[str, Any]:
    """Get performance metrics"""
    with _metrics_lock:
        if component:
            # Filter metrics for specific component
            filtered_metrics = {
                key: dict(value) for key, value in _metrics.items() 
                if key.startswith(f"{component}.")
            }
            return filtered_metrics
        else:
            # Return all metrics
            return {key: dict(value) for key, value in _metrics.items()}

def get_summary_metrics() -> Dict[str, Any]:
    """Get summary of all metrics"""
    with _metrics_lock:
        summary = {
            'total_operations': len(_metrics),
            'total_calls': sum(m['call_count'] for m in _metrics.values()),
            'total_errors': sum(m['errors'] for m in _metrics.values()),
            'components': {},
            'top_slowest_operations': [],
            'most_called_operations': []
        }
        
        # Group by component
        component_stats = defaultdict(lambda: {
            'operations': 0,
            'total_calls': 0,
            'total_errors': 0,
            'avg_time': 0.0
        })
        
        operation_times = []
        operation_calls = []
        
        for key, metrics in _metrics.items():
            component = key.split('.')[0]
            comp_stats = component_stats[component]
            
            comp_stats['operations'] += 1
            comp_stats['total_calls'] += metrics['call_count']
            comp_stats['total_errors'] += metrics['errors']
            comp_stats['avg_time'] += metrics['avg_time']
            
            operation_times.append((key, metrics['avg_time']))
            operation_calls.append((key, metrics['call_count']))
        
        # Calculate component averages
        for component, stats in component_stats.items():
            if stats['operations'] > 0:
                stats['avg_time'] = stats['avg_time'] / stats['operations']
        
        summary['components'] = dict(component_stats)
        
        # Top slowest operations
        summary['top_slowest_operations'] = sorted(
            operation_times, key=lambda x: x[1], reverse=True
        )[:10]
        
        # Most called operations
        summary['most_called_operations'] = sorted(
            operation_calls, key=lambda x: x[1], reverse=True
        )[:10]
        
        return summary

def reset_metrics(component: Optional[str] = None):
    """Reset metrics for all or specific component"""
    with _metrics_lock:
        if component:
            keys_to_remove = [key for key in _metrics.keys() if key.startswith(f"{component}.")]
            for key in keys_to_remove:
                del _metrics[key]
        else:
            _metrics.clear()

class MetricsCollector:
    """Class-based metrics collector for more complex scenarios"""
    
    def __init__(self, component: str):
        self.component = component
        
    def record_operation(self, operation: str, execution_time: float, success: bool = True):
        """Record a manual operation"""
        metric_key = f"{self.component}.{operation}"
        _update_metrics(metric_key, execution_time, success)
        
    def get_component_metrics(self) -> Dict[str, Any]:
        """Get metrics for this component"""
        return get_metrics(self.component)

# Prometheus metrics support
try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server, REGISTRY
    
    # Prometheus metrics - handle duplicates gracefully
    REQUEST_COUNT = None
    REQUEST_DURATION = None
    ACTIVE_REQUESTS = None
    ERROR_COUNT = None
    
    try:
        REQUEST_COUNT = Counter('mseis_requests_total', 'Total requests', ['component', 'operation'])
        REQUEST_DURATION = Histogram('mseis_request_duration_seconds', 'Request duration', ['component', 'operation'])
        ACTIVE_REQUESTS = Gauge('mseis_active_requests', 'Active requests', ['component'])
        ERROR_COUNT = Counter('mseis_errors_total', 'Total errors', ['component', 'operation'])
    except ValueError as e:
        # Metrics already registered, try to get existing ones
        if "Duplicated timeseries" in str(e):
            # Get existing metrics from registry
            for collector in list(REGISTRY._collector_to_names.keys()):
                if hasattr(collector, '_name'):
                    if collector._name == 'mseis_requests_total':
                        REQUEST_COUNT = collector
                    elif collector._name == 'mseis_request_duration_seconds':
                        REQUEST_DURATION = collector
                    elif collector._name == 'mseis_active_requests':
                        ACTIVE_REQUESTS = collector
                    elif collector._name == 'mseis_errors_total':
                        ERROR_COUNT = collector
        else:
            raise e
    
    PROMETHEUS_AVAILABLE = True
    
    def update_prometheus_metrics(component: str, operation: str, execution_time: float, success: bool = True):
        """Update Prometheus metrics"""
        if REQUEST_COUNT:
            REQUEST_COUNT.labels(component=component, operation=operation).inc()
        if REQUEST_DURATION:
            REQUEST_DURATION.labels(component=component, operation=operation).observe(execution_time)
        
        if not success and ERROR_COUNT:
            ERROR_COUNT.labels(component=component, operation=operation).inc()
    
    def start_metrics_server(port: int = 8000):
        """Start Prometheus metrics server"""
        try:
            start_http_server(port)
            logger.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {str(e)}")
            
except ImportError:
    PROMETHEUS_AVAILABLE = False
    
    def update_prometheus_metrics(*args, **kwargs):
        pass
    
    def start_metrics_server(port: int = 8000):
        logger.warning("Prometheus client not available. Metrics server not started.")

# Enhanced monitoring decorator with Prometheus support
def enhanced_monitor(component: str, operation: str):
    """Enhanced monitoring with Prometheus support"""
    
    def decorator(func: Callable) -> Callable:
        metric_key = f"{component}.{operation}"
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                if PROMETHEUS_AVAILABLE:
                    ACTIVE_REQUESTS.labels(component=component).inc()
                
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    _update_metrics(metric_key, execution_time, success=True)
                    
                    if PROMETHEUS_AVAILABLE:
                        update_prometheus_metrics(component, operation, execution_time, success=True)
                    
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    _update_metrics(metric_key, execution_time, success=False)
                    
                    if PROMETHEUS_AVAILABLE:
                        update_prometheus_metrics(component, operation, execution_time, success=False)
                    
                    raise
                finally:
                    if PROMETHEUS_AVAILABLE:
                        ACTIVE_REQUESTS.labels(component=component).dec()
                        
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                if PROMETHEUS_AVAILABLE:
                    ACTIVE_REQUESTS.labels(component=component).inc()
                
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    _update_metrics(metric_key, execution_time, success=True)
                    
                    if PROMETHEUS_AVAILABLE:
                        update_prometheus_metrics(component, operation, execution_time, success=True)
                    
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    _update_metrics(metric_key, execution_time, success=False)
                    
                    if PROMETHEUS_AVAILABLE:
                        update_prometheus_metrics(component, operation, execution_time, success=False)
                    
                    raise
                finally:
                    if PROMETHEUS_AVAILABLE:
                        ACTIVE_REQUESTS.labels(component=component).dec()
                        
            return sync_wrapper
            
    return decorator 