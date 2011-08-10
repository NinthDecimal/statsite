"""
Contains a dumb metrics store used for testing.
"""

class DumbMetricsStore(object):
    def __init__(self):
        self.data = []

    def flush(self, data):
        self.data.extend(data)
