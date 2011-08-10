"""
Contains helper classes and methods for tests.
"""

class DumbAggregator(object):
    def __init__(self):
        self.metrics = []

    def add_metrics(self, metrics):
        self.metrics.extend(metrics)

class DumbMetricsStore(object):
    def __init__(self):
        self.data = []

    def flush(self, data):
        self.data.extend(data)
