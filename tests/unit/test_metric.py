"""
Contains tests for the base metric class.
"""

import statsite.messages as m

class TestMetric(object):
    def test_fold_basic(self):
        """Tests folding over a normal metric returns the key/value
        using the flag as the timestamp."""
        metrics = [m.Metric("k", 27, 123456)]
        assert [("k", 27, 123456)] == m.Metric.fold(metrics, 0)

    def test_fold_uses_now(self):
        """
        Tests that folding over a normal metric with no flag will use
        the "now" time as the timestamp.
        """
        metrics = [m.Metric("k", 27, None)]
        assert [("k", 27, 123456)] == m.Metric.fold(metrics, 123456)
