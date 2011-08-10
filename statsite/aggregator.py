"""
This module implements the aggregator which is
used to collect statistics over a given time interval,
aggregate and then submit to Graphite.
"""
import logging
import time
import threading

class Aggregator(threading.Thread):
    def __init__(self, interval, metrics_store):
        """
        An aggregator simple accumulates metrics until it is started via
        :meth:`start()`. This starts a new thread, in which the stored metrics
        will be aggregated and then flushed to the proper metrics store.

        The aggregator is not designed to be thread safe, meaning only a single
        thread should call :meth:`add_metric()` and once it is started, no more
        calls to :meth:`add_metric()` should be made.

        :Parameters:
            - `metrics_store` : The metrics storage instance to flush to.
        """
        super(Aggregator, self).__init__()
        self.metrics_queue = []
        self.metrics_store = metrics_store
        self.logger = logging.getLogger("statsite.Aggregator")

    def add_metric(self, metric):
        """Adds a new metric to be aggregated"""
        self.metrics_queue.append(metric)

    def run(self):
        """
        Override the threading.Thread implementation to
        instead aggregate the metrics and then flush them.
        """
        self.logger.info("Aggregator started")

        try:
            data = self.aggregate_queue()
        except:
            data = None
            self.logger.exception("Failed to aggregate interval data!")

        try:
            if data: self.metrics_store.flush(data)
        except:
            self.logger.exception("Failed to flush interval data!")

        self.logger.info("Aggregator shutdown")

    def aggregate_queue(self):
        """
        Aggregates our metrics and returns a list of (key,value,timestamp) pairs.
        """
        # Sort the queue by the type of metric
        metric_types = {}
        for metric in self.metrics_queue:
            metric_types.setdefault(type(metric),[])
            metric_types[type(metric)].append(metric)

        # Fold over the metrics by class
        data = []
        now = time.time()
        for cls,raw in metric_types.iteritems():
            aggregated = cls.fold(raw, now)
            data.extend(aggregated)

        return data


class AggregatorProxy(object):
    def __init__(self, interval, metrics_store, aggregator_cls=Aggregator):
        """
        Serves as a proxy to the aggregator that we are using underneath,
        and rotates the aggegator on an interval. This allows us to use a single
        aggregator for a given interval, and then perform the aggregation and flushing
        in a different thread.

        :Parameters:
            - `interval` : The interval to flush on, in seconds.
            - `metrics_store` : The metrics storage instance to use.
            - `aggregator_cls` (optional) : The underlying aggregator implementation
            to use. This defaults to Aggregator.
        """
        if not isinstance(interval, (int,float)): raise ValueError, "Interval must be numeric!"
        if interval <= 0: raise ValueError, "Interval must be positive!"

        # Store the inputs
        self.interval = interval
        self.metrics_store = metrics_store
        self.aggregator_cls = aggregator_cls

        # Create an aggregator and time
        self.aggregator = self.aggregator_cls(self.metrics_store)
        self.create_time = time.time()

    def add_metric(self, metric):
        """
        Adds a new metric object to be aggregated in the future.
        """
        # Check if we need to rotate the aggregator
        now = time.time()
        if now - self.create_time > self.interval:
            self.aggregator.start()
            self.aggregator = self.aggregator_cls(self.metrics_store)
            self.create_time = now

        # Store the metrics
        self.aggregator.add_metric(metric)

