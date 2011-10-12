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

    def __eq__(self, other):
        """
        Equality check for metrics. This does a basic check to make sure
        key, value, and flag are equivalent.
        """
        return isinstance(other, Metric) and \
            self.key == other.key and \
            self.value == other.value and \
            self.flag == other.flag

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
        sample_rate = self.flag if self.flag else 1.0
        accum[self.key] += self.value / (1 / sample_rate)


class Timer(Metric):
    """
    Represents timing metrics, provided by the 'ms' type.
    """
    @classmethod
    def fold(cls, lst, now, percentile=90):
        accumulator = {}
        for item in lst: item._fold(accumulator)

        outputs = []
        for key,vals in accumulator.iteritems():
            # Sort the values
            vals.sort()

            val_count = len(vals)
            val_sum = sum(vals)
            val_avg = float(val_sum) / val_count
            val_min = vals[0]
            val_max = vals[-1]
            val_stdev = cls._stdev(vals, val_avg)

            # Calculate the inner percentile
            inner_indexes = int(len(vals) * (percentile / 100.0))
            lower_idx = (len(vals) - inner_indexes) / 2
            upper_idx = lower_idx + inner_indexes

            # If we only have one item, then the percentile is just the
            # values itself, otherwise the lower_idx:upper_idx slice returns
            # an empty list.
            if len(vals) == 1:
                vals_pct = vals
            else:
                vals_pct = vals[lower_idx:upper_idx]

            val_sum_pct = sum(vals_pct)
            val_avg_pct = val_sum_pct / inner_indexes if inner_indexes > 0 else val_sum_pct
            val_min_pct = vals[lower_idx]
            val_max_pct = vals[upper_idx]
            val_stdev_pct = cls._stdev(vals_pct, val_avg_pct)

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
    def _stdev(cls, lst, lst_avg):
        # Sample size is N-1
        sample_size = float(len(lst) - 1)
        if sample_size == 0 : return 0

        # Calculate the sum of the difference from the
        # mean squared
        diff_sq = sum([(v-lst_avg)**2 for v in lst])

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

    @classmethod
    def fold(cls, lst, now):
        """
        Takes a list of the metrics objects and emits lists of (key,value,timestamp)
        pairs. Adds the kv prefix to all the keys so as not to pollute the main namespace.
        """
        return [("kv.%s" % o.key,o.value,o.flag if o.flag else now) for o in lst]


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

