"""
Contains tests for the Statsite class.
"""

from tests.base import TestBase
from tests.helpers import DumbCollector, DumbAggregator, DumbMetricsStore
from statsite.statsite import Statsite

class TestStatsite(TestBase):
    def pytest_funcarg__statsite_dummy(self, request):
        """
        Returns a Statsite instance where every component is a test dummy.
        """
        return Statsite(collector_cls=DumbCollector,
                        aggregator_cls=DumbAggregator,
                        store_cls=DumbMetricsStore)

    def test_initialization(self, statsite_dummy):
        """
        Tests that initialization properly initializes all the pieces
        of the Statsite architecture.
        """
        assert statsite_dummy.collector
        assert statsite_dummy.aggregator is statsite_dummy.collector.aggregator
        assert statsite_dummy.store is statsite_dummy.aggregator.metrics_store

    def test_flush_and_switch_aggregator(self, statsite_dummy):
        """
        Tests that flushing and switching the aggregator properly
        works.
        """
        original = statsite_dummy.aggregator
        statsite_dummy._flush_and_switch_aggregator()

        assert statsite_dummy.aggregator is statsite_dummy.collector.aggregator
        assert original is not statsite_dummy.aggregator
        assert original.flushed
