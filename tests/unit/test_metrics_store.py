"""
Contains metric store tests.
"""

import pytest
from tests.base import TestBase
from statsite.metrics_store import GraphiteStore, MetricsStore

class TestMetricsStore(TestBase):
    """
    Tests the metrics store base class, but there are no real
    tests for this at the moment since there is only one method
    and it is abstract.
    """
    pass

class TestGraphiteStore(TestBase):
    def test_flushes(self, graphite):
        """
        Tests that metrics are properly flushed to a graphite server.
        """
        store = GraphiteStore(graphite.host, graphite.port)
        metrics = [("k", 1, 10), ("j", 2, 20)]

        # Flush the metrics and verify that graphite sees the
        # proper results
        store.flush(metrics)
        store.close()

        # Check that we get the proper results after a specific
        # flush interval to give the test time to send the data
        def check():
            metric_strings = ["%s %s %s\n" % metric for metric in metrics]
            assert metric_strings == graphite.messages

        self.after_flush_interval(check, interval=1)
