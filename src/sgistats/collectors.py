from .destinations import MetricsDestination
from typing import Any


class MetricsCollector:
    def __init__(self, destinations: list[MetricsDestination]):
        self.destinations = destinations

    def record(self, metric_name: str, value: Any):
        for destination in self.destinations:
            destination.record(metric_name, value)