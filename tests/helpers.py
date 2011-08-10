"""
Contains helper classes and methods for tests.
"""

from statsite.aggregator import Aggregator
from statsite.collector import Collector
from statsite.metrics_store import MetricsStore

class DumbAggregator(Aggregator):
    def __init__(self, *args, **kwargs):
        super(DumbAggregator, self).__init__(*args, **kwargs)

        self.metrics = []

    def add_metrics(self, metrics):
        self.metrics.extend(metrics)

class DumbCollector(Collector):
    pass

class DumbMetricsStore(MetricsStore):
    def __init__(self):
        self.data = []

    def flush(self, data):
        self.data.extend(data)
