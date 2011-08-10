"""
Contains tests for the Counter metric.
"""

from statsite.metrics import Counter

class TestCounterMetric(object):
    def test_fold(self):
        """
        Tests that counter folding places the sum into a
        unique key for each counter.
        """
        metrics = [Counter("k", 10),
                   Counter("k", 15),
                   Counter("j", 5),
                   Counter("j", 15)]
        expected = [("counts.k", 25, 0), ("counts.j", 20, 0)]

        result = Counter.fold(metrics, 0)
        assert expected == result
