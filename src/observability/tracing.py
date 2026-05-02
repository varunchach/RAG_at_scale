# OpenTelemetry Tracing Setup
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.sdk.resources import Resource
from contextlib import contextmanager
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TracingManager:
    def __init__(self, service_name: str = "rag-service",
                 otlp_endpoint: Optional[str] = None):
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint
        self._tracer: trace.Tracer | None = None

    def setup_tracing(self):
        """Configure OpenTelemetry tracing.

        When no OTLP endpoint is configured (local dev / notebook), a Console
        exporter is added so students can see span output in stdout.
        In production, set OTLP_ENDPOINT to point at Jaeger or CloudWatch X-Ray.
        """
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": "1.0.0",
        })

        provider = TracerProvider(resource=resource)

        if self.otlp_endpoint:
            # Lazy import — only needed when exporting over gRPC
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=self.otlp_endpoint, insecure=True)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info("OTLP tracing → %s", self.otlp_endpoint)
        else:
            # Human-readable console output for demos. Use a simple processor so
            # span logs appear in the same notebook section that generated them.
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
            logger.info("Tracing → console (no OTLP endpoint configured)")

        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer(__name__)
        return self._tracer

    def get_tracer(self) -> trace.Tracer:
        if self._tracer is None:
            self.setup_tracing()
        return self._tracer


# Global singleton
tracing_manager = TracingManager()


# ------------------------------------------------------------------ #
# Convenience context managers (notebook-friendly)                   #
# ------------------------------------------------------------------ #

@contextmanager
def trace_span(name: str, **attributes):
    """Generic span context manager — yields the active span."""
    tracer = tracing_manager.get_tracer()
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield span


@contextmanager
def trace_embedding_generation(doc_count: int):
    """Trace an embedding-generation batch."""
    with trace_span("embedding_generation", doc_count=doc_count) as span:
        yield span


@contextmanager
def trace_search_query(query_length: int):
    """Trace a hybrid search call."""
    with trace_span("search_query", query_length=query_length) as span:
        yield span


@contextmanager
def trace_reranking(candidates_count: int, final_count: int):
    """Trace a reranking pass."""
    with trace_span("reranking",
                    candidates_count=candidates_count,
                    final_count=final_count) as span:
        yield span
