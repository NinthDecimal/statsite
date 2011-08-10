"""
Contains tests for the statistics aggregator base class as well
as the default aggregator class.
"""

import time
from tests.base import TestBase
from statsite.aggregator import Aggregator, DefaultAggregator
from statsite.metrics import Counter, KeyValue

class TestAggregator(TestBase):
    def test_fold_metrics_works(self, monkeypatch):
        """
        Tests that aggregators can fold metrics properly.
        """
        now = 12
        monkeypatch.setattr(time, 'time', lambda: now)
        metrics  = [KeyValue("k", 1, now), Counter("j", 2)]
        result   = Aggregator(None)._fold_metrics(metrics)

        assert 1 == result.count(("k", 1, now))
        assert 1 == result.count(("counts.j", 2, now))

class TestDefaultAggregator(TestBase):
    def test_flushes_collected_metrics(self, metrics_store):
        """
        Tests that the default aggregator properly flushes the
        collected metrics to the metric store.
        """
        now = 17
        agg = DefaultAggregator(metrics_store)
        agg.add_metrics([KeyValue("k", 1, now)])
        agg.add_metrics([KeyValue("k", 2, now)])
        agg.flush()

        assert [("k", 1, now), ("k", 2, now)] == metrics_store.data
