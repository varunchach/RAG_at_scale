# Prometheus Metrics
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time
from typing import Callable
import logging

logger = logging.getLogger(__name__)

class MetricsManager:
    def __init__(self):
        self._metrics_server_started = False
        self._metrics_server_port: int | None = None
        # Counters
        self.requests_total = Counter(
            'rag_requests_total',
            'Total number of requests',
            ['method', 'endpoint', 'status']
        )

        self.embeddings_generated = Counter(
            'rag_embeddings_generated_total',
            'Total number of embeddings generated'
        )

        self.searches_performed = Counter(
            'rag_searches_performed_total',
            'Total number of searches performed'
        )

        # Histograms
        self.request_duration = Histogram(
            'rag_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )

        self.embedding_duration = Histogram(
            'rag_embedding_duration_seconds',
            'Embedding generation duration'
        )

        self.search_duration = Histogram(
            'rag_search_duration_seconds',
            'Search duration'
        )

        # Gauges
        self.active_connections = Gauge(
            'rag_active_connections',
            'Number of active connections'
        )

        self.index_size = Gauge(
            'rag_index_size',
            'Size of the document index'
        )

    def start_server(self, port: int = 8001):
        """Start Prometheus metrics server"""
        if self._metrics_server_started:
            logger.info(
                "Prometheus metrics server already running on port %s",
                self._metrics_server_port,
            )
            return

        try:
            start_http_server(port)
        except OSError as exc:
            if self._metrics_server_port == port:
                logger.info("Prometheus metrics server already bound on port %s", port)
                self._metrics_server_started = True
                return
            raise exc

        self._metrics_server_started = True
        self._metrics_server_port = port
        logger.info(f"Prometheus metrics server started on port {port}")

    def measure_time(self, metric: Histogram) -> Callable:
        """Decorator to measure execution time"""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metric.observe(duration)
                return result
            return wrapper
        return decorator

# Global metrics instance
metrics = MetricsManager()

# Convenience decorators
def measure_request_time(method: str, endpoint: str):
    """Decorator for measuring request time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            metrics.request_duration.labels(method=method, endpoint=endpoint).observe(duration)
            return result
        return wrapper
    return decorator

def measure_embedding_time():
    """Decorator for measuring embedding generation time"""
    return metrics.measure_time(metrics.embedding_duration)

def measure_search_time():
    """Decorator for measuring search time"""
    return metrics.measure_time(metrics.search_duration)
