"""
Contains tests for the timer metric.
"""

from statsite.metrics import Timer

class TestTimerMetric(object):
    def test_fold_sum(self):
        """
        Tests that folding generates a sum of the timers.
        """
        now = 10
        metrics = [Timer("k", 10),
                   Timer("k", 15),
                   Timer("j", 7),
                   Timer("j", 8)]
        result = Timer.fold(metrics, now)

        assert ("timers.k.sum", 25, now) == self._get_metric("timers.k.sum", result)
        assert ("timers.j.sum", 15, now) == self._get_metric("timers.j.sum", result)

    def test_fold_mean(self):
        """
        Tests that the mean is properly generated for the
        timers.
        """
        now = 10
        metrics = [Timer("k", 10),
                   Timer("k", 15),
                   Timer("j", 7),
                   Timer("j", 8)]
        result = Timer.fold(metrics, now)

        assert ("timers.k.mean", 12.5, now) == self._get_metric("timers.k.mean", result)
        assert ("timers.j.mean", 7.5, now) == self._get_metric("timers.j.mean", result)

    def _get_metric(self, key, metrics):
        """
        This will extract a specific metric out of an array of metrics.
        """
        for metric in metrics:
            if metric[0] == key:
                return metric

        return None
