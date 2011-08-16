"""
Contains helper classes and methods for tests.
"""

from statsite.aggregator import Aggregator
from statsite.collector import Collector
from statsite.metrics_store import MetricsStore

class DumbAggregator(Aggregator):
    def __init__(self, *args, **kwargs):
        super(DumbAggregator, self).__init__(*args, **kwargs)

        self.flushed = False
        self.metrics = []

    def add_metrics(self, metrics):
        self.metrics.extend(metrics)

    def flush(self):
        self.flushed = True

class DumbCollector(Collector):
    pass

class DumbMetricsStore(MetricsStore):
    def __init__(self):
        self.data = []

    def flush(self, data):
        self.data.extend(data)

def statsite_settings(settings):
    """
    Decorator to set the settings for Statsite for the "servers"
    funcarg.
    """
    def decorator(func):
        func.func_dict["statsite_settings"] = settings
        return func

    return decorator
