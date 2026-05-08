import logging
import os
import time
from typing import Callable

import boto3
from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = logging.getLogger(__name__)


class MetricsManager:
    def __init__(self):
        self._metrics_server_started = False
        self._metrics_server_port: int | None = None
        self._cloudwatch_client = None
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

    def _cloudwatch_metrics_enabled(self) -> bool:
        return os.environ.get("ENABLE_CLOUDWATCH_APP_METRICS", "false").lower() == "true"

    def _metric_namespace(self) -> str:
        return os.environ.get("CLOUDWATCH_METRIC_NAMESPACE", "RAGAtScale/Application")

    def _service_dimensions(self, route: str) -> list[dict[str, str]]:
        return [
            {"Name": "Service", "Value": os.environ.get("SERVICE_NAME", "rag-at-scale-service")},
            {"Name": "Route", "Value": route},
        ]

    def _get_cloudwatch_client(self):
        if not self._cloudwatch_metrics_enabled():
            return None
        if self._cloudwatch_client is None:
            self._cloudwatch_client = boto3.client(
                "cloudwatch",
                region_name=os.environ.get("AWS_REGION", "us-east-1"),
            )
        return self._cloudwatch_client

    def _put_metric_batch(self, metric_data: list[dict]):
        if not metric_data:
            return
        client = self._get_cloudwatch_client()
        if client is None:
            return

        for i in range(0, len(metric_data), 20):
            chunk = metric_data[i : i + 20]
            try:
                client.put_metric_data(
                    Namespace=self._metric_namespace(),
                    MetricData=chunk,
                )
            except Exception:
                logger.exception("Failed to publish CloudWatch metric batch")

    def publish_search_metrics(
        self,
        route: str,
        retrieval_count: int,
        reranked_count: int,
        search_time: float,
        rerank_time: float | None,
        generation_time: float | None,
        total_time: float,
    ):
        metric_data = [
            {
                "MetricName": "RetrievalChunkCount",
                "Dimensions": self._service_dimensions(route),
                "Unit": "Count",
                "Value": retrieval_count,
            },
            {
                "MetricName": "RerankedChunkCount",
                "Dimensions": self._service_dimensions(route),
                "Unit": "Count",
                "Value": reranked_count,
            },
            {
                "MetricName": "SearchLatencyMs",
                "Dimensions": self._service_dimensions(route),
                "Unit": "Milliseconds",
                "Value": search_time * 1000,
            },
            {
                "MetricName": "EndToEndLatencyMs",
                "Dimensions": self._service_dimensions(route),
                "Unit": "Milliseconds",
                "Value": total_time * 1000,
            },
        ]

        if rerank_time is not None:
            metric_data.append(
                {
                    "MetricName": "RerankLatencyMs",
                    "Dimensions": self._service_dimensions(route),
                    "Unit": "Milliseconds",
                    "Value": rerank_time * 1000,
                }
            )

        if generation_time is not None:
            metric_data.append(
                {
                    "MetricName": "GenerationLatencyMs",
                    "Dimensions": self._service_dimensions(route),
                    "Unit": "Milliseconds",
                    "Value": generation_time * 1000,
                }
            )

        self._put_metric_batch(metric_data)

    def publish_eval_sample_count(self, route: str):
        self._put_metric_batch(
            [
                {
                    "MetricName": "EvalSampleCount",
                    "Dimensions": self._service_dimensions(route),
                    "Unit": "Count",
                    "Value": 1,
                }
            ]
        )

    def publish_judge_failure(self, route: str):
        self._put_metric_batch(
            [
                {
                    "MetricName": "JudgeFailureCount",
                    "Dimensions": self._service_dimensions(route),
                    "Unit": "Count",
                    "Value": 1,
                }
            ]
        )

    def publish_eval_scores(self, route: str, scores: dict[str, float]):
        metric_names = {
            "faithfulness": "FaithfulnessScore",
            "context_precision": "ContextPrecisionScore",
            "context_coverage": "ContextCoverageScore",
            "answer_relevancy": "AnswerRelevancyScore",
        }
        metric_data = []
        for key, metric_name in metric_names.items():
            if key not in scores:
                continue
            metric_data.append(
                {
                    "MetricName": metric_name,
                    "Dimensions": self._service_dimensions(route),
                    "Unit": "None",
                    "Value": scores[key],
                }
            )

        self._put_metric_batch(metric_data)

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
