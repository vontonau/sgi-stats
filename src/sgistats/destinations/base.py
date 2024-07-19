from typing import Protocol, Any


class MetricsDestination(Protocol):
    def record(self, metric_name: str, value: Any):
        pass


class ConsoleMetricsDestination(MetricsDestination):
    def record(self, metric_name: str, value: Any):
        print(f"Metric: {metric_name}, Value: {value}")