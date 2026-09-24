"""Privacy-minimized Azure Monitor hooks for the synthetic demo."""
import os
import time
from pathlib import Path

_meter = None
_requests = None
_duration = None
_configured = False


def configure():
    """Enable custom aggregate telemetry only when a connection string exists."""
    global _meter, _requests, _duration, _configured
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
        from opentelemetry import metrics
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
