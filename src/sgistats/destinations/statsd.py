from base import MetricsDestination
from typing import Any


class StatsDMetricsDestination(MetricsDestination):
    def __init__(self, client):
        self.client = client

    def record(self, metric_name: str, value: int | float | str | Any):
        if isinstance(value, (int, float)):
            self.client.gauge(metric_name, value)
        elif isinstance(value, str):
            if value.isdigit():
                self.client.gauge(metric_name, int(value))
            else:
                self.client.incr(f"{metric_name}.{value}")
        else:
            # For other types, just increment a counter with the metric name
            self.client.incr(metric_name)
