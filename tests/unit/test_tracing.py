import pytest
from unittest.mock import patch, MagicMock
from flowcore.observability.tracing import setup_tracing, get_tracer

def test_setup_tracing_disabled(monkeypatch):
    monkeypatch.setenv("OTEL_ENABLED", "false")
    with patch("flowcore.observability.tracing.TracerProvider") as mock_provider:
        setup_tracing()
        mock_provider.assert_not_called()

def test_setup_tracing_default(monkeypatch):
    monkeypatch.delenv("OTEL_ENABLED", raising=False)
    monkeypatch.delenv("OTEL_SERVICE_NAME", raising=False)
    
    with patch("flowcore.observability.tracing.Resource") as mock_resource, \
         patch("flowcore.observability.tracing.TracerProvider") as mock_provider, \
         patch("flowcore.observability.tracing.OTLPSpanExporter") as mock_exporter, \
         patch("flowcore.observability.tracing.BatchSpanProcessor") as mock_processor, \
         patch("flowcore.observability.tracing.trace.set_tracer_provider") as mock_set_provider:
        
        setup_tracing()
        
        mock_resource.create.assert_called_once_with({"service.name": "flowcore"})
        mock_provider.assert_called_once()
        mock_exporter.assert_called_once_with(endpoint="http://jaeger:4317", insecure=True)
        mock_processor.assert_called_once()
        mock_set_provider.assert_called_once()

def test_setup_tracing_custom_service_name_arg(monkeypatch):
    with patch("flowcore.observability.tracing.Resource") as mock_resource, \
         patch("flowcore.observability.tracing.TracerProvider"), \
         patch("flowcore.observability.tracing.OTLPSpanExporter"), \
         patch("flowcore.observability.tracing.BatchSpanProcessor"), \
         patch("flowcore.observability.tracing.trace.set_tracer_provider"):
        
        setup_tracing(service_name="custom-service")
        mock_resource.create.assert_called_once_with({"service.name": "custom-service"})

def test_setup_tracing_custom_endpoint(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://custom:4317")
    with patch("flowcore.observability.tracing.Resource"), \
         patch("flowcore.observability.tracing.TracerProvider"), \
         patch("flowcore.observability.tracing.OTLPSpanExporter") as mock_exporter, \
         patch("flowcore.observability.tracing.BatchSpanProcessor"), \
         patch("flowcore.observability.tracing.trace.set_tracer_provider"):
        
        setup_tracing()
        mock_exporter.assert_called_once_with(endpoint="http://custom:4317", insecure=True)

def test_get_tracer_returns_tracer():
    tracer = get_tracer("test.module")
    assert hasattr(tracer, "start_as_current_span")
