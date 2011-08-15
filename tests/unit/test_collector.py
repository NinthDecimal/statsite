"""
Contains tests for the collector base class.
"""

import pytest
from tests.base import TestBase
from statsite.metrics import Counter, KeyValue, Timer
from statsite.collector import Collector

class TestCollector(TestBase):
    def test_stores_aggregator(self):
        """
        Tests that collectors will store aggregator objects.
        """
        agg = object()
        assert agg is Collector(agg).aggregator

    def test_parse_metrics_succeeds(self):
        """
        Tests that parsing metrics succeeds and returns an array
        of proper metric objects.
        """
        message = "\n".join(["k:1|kv", "j:27|ms"])
        results = Collector(None).parse_metrics(message)

        assert isinstance(results[0], KeyValue)
        assert isinstance(results[1], Timer)

    def test_parse_metrics_suppress_error(self):
        """
        Tests that parsing metrics will suppress errors if requested.
        """
        message = "k:1|nope"
        results = Collector(None).parse_metrics(message)

        assert 0 == len(results)

    def test_parse_metrics_keeps_good_metrics(self, aggregator):
        """
        Tests that parse_metrics will keep the good metrics in the face
        of an error.
        """
        message = "\n".join(["k::1|c",
                             "j:2|nope",
                             "k:2|ms"])
        results = Collector(aggregator).parse_metrics(message)

        assert [Timer("k", 2)] == results

    def test_parse_metrics_ignores_blank_lines(self, aggregator):
        """
        Tests that parse_metrics will properly ignore blank lines.
        """
        message = "\n".join(["", "k:2|ms"])
        assert [Timer("k", 2)] == Collector(aggregator).parse_metrics(message)

    def test_add_metrics(self, aggregator):
        """
        Tests that add_metrics successfully adds an array of metrics to
        the configured aggregator.
        """
        now = 17
        metrics = [KeyValue("k", 1, now), Counter("j", 2)]
        Collector(aggregator).add_metrics(metrics)

        assert metrics == aggregator.metrics

    def test_set_aggregator(self, aggregator):
        """
        Tests that setting an aggregator properly works.
        """
        coll    = Collector(aggregator)
        new_agg = object()

        assert aggregator is coll.aggregator
        coll.set_aggregator(new_agg)
        assert new_agg is coll.aggregator
