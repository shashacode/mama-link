"""Privacy-minimized Azure Monitor hooks for the synthetic demo."""
from contextlib import contextmanager
import os
import time
from pathlib import Path

_meter = None
_requests = None
_duration = None
_tracer = None
_configured = False


def configure():
    """Enable aggregate metrics and metadata-only spans when configured."""
    global _meter, _requests, _duration, _tracer, _configured
    if _configured:
        return True
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    except ImportError:
        pass
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING", "").strip()
    if not connection_string:
        return False
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry import metrics, trace
    except ImportError:
        return False
    configure_azure_monitor(
        connection_string=connection_string,
        instrumentation_options={
            "azure_sdk": {"enabled": False},
            "django": {"enabled": False},
            "fastapi": {"enabled": False},
            "flask": {"enabled": False},
            "psycopg2": {"enabled": False},
            "requests": {"enabled": False},
            "urllib": {"enabled": False},
            "urllib3": {"enabled": False},
        },
    )
    _meter = metrics.get_meter("mama_link.synthetic_demo")
    _tracer = trace.get_tracer("mama_link.synthetic_demo")
    _requests = _meter.create_counter("mama_link.operations")
    _duration = _meter.create_histogram("mama_link.operation.duration", unit="ms")
    _configured = True
    return True


def record(operation, status, started):
    """Record allow-listed aggregate fields; never accept request or case data."""
    if not _requests:
        return
    attributes = {"operation": operation, "status": status}
    _requests.add(1, attributes)
    _duration.record((time.perf_counter() - started) * 1000, attributes)


@contextmanager
def agent_span(agent_name, agent_version, role):
    """Trace an agent invocation without recording prompts, outputs, or profile data."""
    if not _tracer:
        yield None
        return
    with _tracer.start_as_current_span("invoke_agent") as span:
        span.set_attribute("gen_ai.operation.name", "invoke_agent")
        span.set_attribute("gen_ai.agent.name", str(agent_name))
        span.set_attribute("gen_ai.agent.id", str(agent_name))
        span.set_attribute("gen_ai.agent.version", str(agent_version))
        span.set_attribute("mama_link.agent.role", str(role))
        span.set_attribute("mama_link.synthetic_data", True)
        yield span


def force_flush(timeout_millis=10000):
    """Flush pending telemetry before short-lived CLI commands exit."""
    try:
        from opentelemetry import metrics, trace
        trace_provider = trace.get_tracer_provider()
        meter_provider = metrics.get_meter_provider()
        if hasattr(trace_provider, "force_flush"):
            trace_provider.force_flush(timeout_millis=timeout_millis)
        if hasattr(meter_provider, "force_flush"):
            meter_provider.force_flush(timeout_millis=timeout_millis)
    except Exception:
        return False
    return True
