import os
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

def setup_tracing(service_name: str = None):
    enabled = os.getenv("OTEL_ENABLED", "true").lower() == "true"
    if not enabled:
        return

    service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "flowcore")
    
    resource = Resource.create({
        "service.name": service_name,
    })

    provider = TracerProvider(resource=resource)
    
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    
    trace.set_tracer_provider(provider)

def get_tracer(name: str):
    return trace.get_tracer(name)
