"""
The module implements the Metric class and its
sub-classes. These are used to wrap the values in the
incoming messages, and contain them in classes of
the proper type.
"""
import math
import time

class Metric(object):
    def __init__(self, key, value, flag=None):
        """
        Represents a base metric. This is not used directly,
        and is instead invoked from sub-classes that are typed
        by the metric.

        Each sub-class must implement a class method :meth:`fold()`
        which takes a list of objects of the same type and returns a list
        of (key,value,timestamp) pairs.

        :Parameters:
            - `key` : The key of the metric
            - `value` : The metric value
            - `flag` (optional) : An optional metric flag. This is specific
            to the flag and has no inherint meaning. For example the Counter
            metric uses this to indicate a sampling rate.
        """
        self.key = key
        self.value = value
        self.flag = flag

    @classmethod
    def fold(cls, lst, now):
        """
        Takes a list of the metrics objects and emits lists of (key,value,timestamp)
        pairs.

        :Parameters:
            - `lst` : A list of metrics objects
            - `now` : The time at which folding started
        """
        return [(o.key,o.value,o.flag if o.flag else now) for o in lst]


class Counter(Metric):
    """
    Represents counter metrics, provided by 'c' type.
    """
    @classmethod
    def fold(cls, lst, now):
        accumulator = {}
        for item in lst: item._fold(accumulator)
        return [("counts.%s" % key,value,now) for key,value in accumulator.iteritems()]

    def _fold(self, accum):
        accum.setdefault(self.key, 0)
        accum[self.key] += self.value


class Timer(Metric):
    """
    Represents timing metrics, provided by the 'ms' type.
    """
    @classmethod
    def fold(cls, lst, now):
        accumulator = {}
        for item in lst: item._fold(accumulator)

        outputs = []
        for key,vals in accumulator.itemitems():
            # Sort the values
            vals.sort()

            val_count = len(vals)
            val_sum = sum(vals)
            val_avg = val_sum / val_count
            val_min = vals[0]
            val_max = vals[-1]
            val_stdev = cls.stdev(vals, val_sum)

            # Calculate the inner percentile
            percentile = 90
            inner_indexes = int(len(vals) * (percentile / 100))
            lower_idx = (len(vals) - inner_indexes) / 2
            upper_idx = lower_idx + inner_indexes

            val_sum_pct = sum(vals[lower_idx:upper_idx])
            val_avg_pct = val_sum_pct / inner_indexes
            val_min_pct = vals[lower_idx]
            val_max_pct = vals[upper_idx]
            val_stdev_pct = cls.stdev(vals[lower_idx:upper_idx], val_sum_pct)

            outputs.append(("timers.%s.sum" % key, val_sum, now))
            outputs.append(("timers.%s.mean" % key, val_avg, now))
            outputs.append(("timers.%s.lower" % key, val_min, now))
            outputs.append(("timers.%s.upper" % key, val_max, now))
            outputs.append(("timers.%s.count" % key, val_count, now))
            outputs.append(("timers.%s.stdev" % key, val_stdev, now))

            outputs.append(("timers.%s.sum_%d" % (key, percentile), val_sum_pct, now))
            outputs.append(("timers.%s.mean_%d" % (key, percentile), val_avg_pct, now))
            outputs.append(("timers.%s.lower_%d" % (key, percentile), val_min_pct, now))
            outputs.append(("timers.%s.upper_%d" % (key, percentile), val_max_pct, now))
            outputs.append(("timers.%s.count_%d" % (key, percentile), inner_indexes, now))
            outputs.append(("timers.%s.stdev_%d" % (key, percentile), val_stdev_pct, now))

        return outputs

    @classmethod
    def _stdev(cls, lst, sum):
        # Calculate the sum of the difference from the
        # mean squared
        diff_sq = sum([(v-sum)**2 for v in lst])

        # Sample size is N-1
        sample_size = len(lst) - 1

        # Take the sqrt of the ratio, that is the stdev
        return math.sqrt(diff_sq / sample_size)

    def _fold(self, accum):
        accum.setdefault(self.key, [])
        accum[self.key].append(self.value)

class KeyValue(Metric):
    """
    Represents a key/value metric, provided by the 'kv' type.
    """
    def __init__(self,key, value, flag=None):
        super(KeyValue, self).__init__(key,value,flag)

        # Set the flag to the current time if not set
        if flag is None: self.flag = time.time()


METRIC_TYPES = {
    "c": Counter,
    "ms": Timer,
    "kv": KeyValue,
}
"""
This dictionary maps the metric type short names
which are specified in the incoming messages to a
class which implements that Metric type. If a short
code is not in this dictionary it is not supported.
"""
