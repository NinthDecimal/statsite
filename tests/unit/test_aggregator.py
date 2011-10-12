"""
Contains tests for the statistics aggregator base class as well
as the default aggregator class.
"""

import time
from tests.base import TestBase
from statsite.aggregator import Aggregator, DefaultAggregator
from statsite.metrics import Counter, KeyValue, Timer

class TestAggregator(TestBase):
    def test_fold_metrics_works(self, monkeypatch):
        """
        Tests that aggregators can fold metrics properly.
        """
        now = 12
        monkeypatch.setattr(time, 'time', lambda: now)
        metrics  = [KeyValue("k", 1, now), Counter("j", 2)]
        result   = Aggregator(None)._fold_metrics(metrics)

        assert 1 == result.count(("kv.k", 1, now))
        assert 1 == result.count(("counts.j", 2, now))

    def test_fold_metrics_passes_metric_settings(self, monkeypatch):
        """
        Tests that aggregators pass the proper metric settings when
        folding over.
        """
        now = 12
        settings = { "ms": { "percentile": 80 } }
        metrics  = [Timer("k", 20, now)]

        monkeypatch.setattr(time, 'time', lambda: now)
        result = Aggregator(None, metrics_settings=settings)._fold_metrics(metrics)
        print repr(result)
        assert 1 == result.count(("timers.k.sum_80", 20, now))

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

        assert [("kv.k", 1, now), ("kv.k", 2, now)] == metrics_store.data
