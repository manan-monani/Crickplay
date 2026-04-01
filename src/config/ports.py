"""
Crickplay Port Registry

Centralized registry of all ports used by services in the Crickplay project.
This ensures no port conflicts and makes configuration easy.

Usage:
    from src.config.ports import PORTS, get_port, get_service_url

    # Get a port
    port = get_port("STREAMLIT_DASHBOARD")

    # Get full URL
    url = get_service_url("FASTAPI_MAIN")
"""

from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ServicePort:
    """Represents a service port configuration."""

    port: int
    description: str
    protocol: str = "http"
    host: str = "localhost"
    container_port: Optional[int] = None  # Internal port in Docker container


# === PORT REGISTRY ===
# All ports should be defined here to avoid conflicts

PORTS: Dict[str, ServicePort] = {
    # =============================================
    # INFRASTRUCTURE SERVICES (Docker Compose)
    # =============================================
    "ZOOKEEPER": ServicePort(
        port=22181,
        container_port=2181,
        description="Apache Zookeeper for Kafka coordination",
    ),
    "KAFKA_EXTERNAL": ServicePort(
        port=29092,
        container_port=9092,
        description="Apache Kafka broker (external access)",
    ),
    "KAFKA_INTERNAL": ServicePort(
        port=9092,
        description="Apache Kafka broker (internal/Docker network)",
    ),
    "POSTGRES": ServicePort(
        port=5432,
        description="PostgreSQL database",
    ),
    "REDIS": ServicePort(
        port=6379,
        description="Redis cache",
    ),
    "KAFKA_UI": ServicePort(
        port=8080,
        description="Kafka UI web interface",
    ),
    # =============================================
    # APPLICATION SERVICES
    # =============================================
    "FASTAPI_MAIN": ServicePort(
        port=8000,
        description="Main FastAPI backend API",
    ),
    "FASTAPI_LIVE_MATCH": ServicePort(
        port=8001,
        description="Live Match SSE streaming API",
    ),
    "STREAMLIT_DASHBOARD": ServicePort(
        port=2424,
        description="Match Simulator Control Dashboard (Streamlit)",
    ),
    "MLFLOW_UI": ServicePort(
        port=5000,
        description="MLflow experiment tracking UI",
    ),
    "RAY_SERVE": ServicePort(
        port=8265,
        description="Ray Serve ML inference endpoint",
    ),
    # =============================================
    # MONITORING & OBSERVABILITY
    # =============================================
    "PROMETHEUS": ServicePort(
        port=9090,
        description="Prometheus metrics server",
    ),
    "GRAFANA": ServicePort(
        port=3000,
        description="Grafana dashboards",
    ),
    "DBT_DOCS": ServicePort(
        port=8580,
        description="dbt documentation server",
    ),
    # =============================================
    # PIPELINE SERVICES
    # =============================================
    "BRONZE_SINK": ServicePort(
        port=8010,
        description="Bronze layer Kafka sink service",
    ),
    "SILVER_TRANSFORMER": ServicePort(
        port=8011,
        description="Silver layer transformation service",
    ),
    "GOLD_BUILDER": ServicePort(
        port=8012,
        description="Gold layer Star Schema builder service",
    ),
    # =============================================
    # FRONTEND
    # =============================================
    "NEXTJS_FRONTEND": ServicePort(
        port=3001,
        description="Next.js frontend application",
    ),
}


def get_port(service_name: str) -> int:
    """Get the port number for a service."""
    if service_name not in PORTS:
        raise ValueError(
            f"Unknown service: {service_name}. Available: {list(PORTS.keys())}"
        )
    return PORTS[service_name].port


def get_service_url(service_name: str, path: str = "") -> str:
    """Get the full URL for a service."""
    service = PORTS.get(service_name)
    if not service:
        raise ValueError(f"Unknown service: {service_name}")
    return f"{service.protocol}://{service.host}:{service.port}{path}"


def get_container_port(service_name: str) -> Optional[int]:
    """Get the container port for a Docker service."""
    service = PORTS.get(service_name)
    return service.container_port if service else None


def print_port_registry():
    """Print a formatted view of all registered ports."""
    print("\n" + "=" * 70)
    print("CRICKPLAY PORT REGISTRY")
    print("=" * 70)

    categories = {
        "Infrastructure": [
            "ZOOKEEPER",
            "KAFKA_EXTERNAL",
            "KAFKA_INTERNAL",
            "POSTGRES",
            "REDIS",
            "KAFKA_UI",
        ],
        "Application": [
            "FASTAPI_MAIN",
            "FASTAPI_LIVE_MATCH",
            "STREAMLIT_DASHBOARD",
            "MLFLOW_UI",
            "RAY_SERVE",
        ],
        "Monitoring": ["PROMETHEUS", "GRAFANA", "DBT_DOCS"],
        "Pipeline": ["BRONZE_SINK", "SILVER_TRANSFORMER", "GOLD_BUILDER"],
        "Frontend": ["NEXTJS_FRONTEND"],
    }

    for category, services in categories.items():
        print(f"\n{category}:")
        print("-" * 50)
        for svc in services:
            if svc in PORTS:
                p = PORTS[svc]
                container = (
                    f" (container: {p.container_port})" if p.container_port else ""
                )
                print(f"  {svc:25} : {p.port:5}{container}")
                print(f"    └─ {p.description}")

    print("\n" + "=" * 70)


# Export Kafka configuration for convenience
KAFKA_CONFIG = {
    "bootstrap_servers": f"localhost:{get_port('KAFKA_EXTERNAL')}",
    "topic_deliveries": "live_match_deliveries",
    "topic_match_events": "match_events",
    "topic_dlq": "live_match_deliveries.dlq",
}


if __name__ == "__main__":
    print_port_registry()
