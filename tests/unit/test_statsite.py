"""
Contains tests for the Statsite class.
"""

from tests.base import TestBase
from tests.helpers import DumbCollector, DumbAggregator, DumbMetricsStore
from statsite.statsite import Statsite

class TestStatsite(TestBase):
    def test_initialization(self):
        """
        Tests that initialization properly initializes all the pieces
        of the Statsite architecture.
        """
        s = Statsite(collector=DumbCollector,
                     aggregator=DumbAggregator,
                     store=DumbMetricsStore)
        assert s.collector
        assert s.aggregator is s.collector.aggregator
        assert s.store is s.aggregator.metrics_store
