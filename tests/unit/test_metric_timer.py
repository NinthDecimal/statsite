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
                   Timer("j", 7.4),
                   Timer("j", 8.6)]
        result = Timer.fold(metrics, now)

        assert ("timers.k.sum", 25, now) == self._get_metric("timers.k.sum", result)
        assert ("timers.j.sum", 16.0, now) == self._get_metric("timers.j.sum", result)

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

    def test_fold_lower(self):
        """
        Tests that the lower bound for the timers is properly computed.
        """
        now = 10
        metrics = [Timer("k", 10),
                   Timer("k", 15),
                   Timer("j", 7.9),
                   Timer("j", 8)]
        result = Timer.fold(metrics, now)

        assert ("timers.k.lower", 10, now) == self._get_metric("timers.k.lower", result)
        assert ("timers.j.lower", 7.9, now) == self._get_metric("timers.j.lower", result)

    def test_fold_upper(self):
        """
        Tests that the upper bound for the timers is properly computed.
        """
        now = 10
        metrics = [Timer("k", 10),
                   Timer("k", 15),
                   Timer("j", 7.9),
                   Timer("j", 8)]
        result = Timer.fold(metrics, now)

        assert ("timers.k.upper", 15, now) == self._get_metric("timers.k.upper", result)
        assert ("timers.j.upper", 8, now) == self._get_metric("timers.j.upper", result)

    def test_fold_count(self):
        """
        Tests the counter of timers is properly computed.
        """
        now = 10
        metrics = [Timer("k", 10),
                   Timer("k", 15),
                   Timer("j", 7.9),
                   Timer("j", 8)]
        result = Timer.fold(metrics, now)

        assert ("timers.k.count", 2, now) == self._get_metric("timers.k.count", result)
        assert ("timers.j.count", 2, now) == self._get_metric("timers.j.count", result)

    def test_fold_stdev(self):
        """
        Tests the standard deviations of counters is properly computed.
        """
        now = 10
        metrics = [Timer("k", 10),
                   Timer("k", 15),
                   Timer("j", 7.9),
                   Timer("j", 8)]
        result = Timer.fold(metrics, now)

        assert ("timers.k.stdev", Timer._stdev([10, 15], 12.5), now) == self._get_metric("timers.k.stdev", result)
        assert ("timers.j.stdev", Timer._stdev([7.9, 8], 7.95), now) == self._get_metric("timers.j.stdev", result)

    def test_stdev(self):
        """
        Tests that the standard deviation is properly computed.
        """
        numbers = [0.331002, 0.591082, 0.668996, 0.422566, 0.458904,
                   0.868717, 0.30459, 0.513035, 0.900689, 0.655826]
        average = sum(numbers) / len(numbers)

        assert int(0.205767 * 10000) == int(Timer._stdev(numbers, average) * 10000)

    def _get_metric(self, key, metrics):
        """
        This will extract a specific metric out of an array of metrics.
        """
        for metric in metrics:
            if metric[0] == key:
                return metric

        return None
