"""
This module implements the aggregator which is
used to collect statistics over a given time interval,
aggregate and then submit to Graphite.
"""
import logging
import Queue
import time
import threading

class Aggregator(threading.Thread):
    def __init__(self, interval):
        super(Aggregator, self).__init__()
        if not isinstance(interval, (int,float)): raise ValueError, "Interval must be numeric!"
        if interval <= 0: raise ValueError, "Interval must be positive!"

        # Store the rotation interval
        self.interval = interval

        # Store the metrics queue and creation time
        self.metrics_queue = Queue.Queue()
        self.queue_time = time.time()

        # Should be running for now
        self.should_run = True

        # Create a logger
        self.logger = logging.getLogger("statsite.Aggregator")

    def add_metric(self, metric):
        # Push the metric into our queue
        self.metrics_queue.put(metric)

    def shutdown(self):
        """Instructs the aggregator to begin shutting down"""
        self.should_run = False
        self.logger.info("Shutdown triggered")

    def run(self):
        self.logger.info("Aggregator started")
        while self.should_run:
            try:
                self._wait_for_interval()
                queue = self._swap_queues()
                data = self._aggregate_queue(queue)
                self._flush_metrics(data)
            except:
                self.logger.exception("Failed to aggregate interval data!")

        self.logger.info("Aggregator shutdown")

    def _wait_for_interval(self):
        """Blocks execution until the next aggregation interval"""
        time.sleep(self.interval)

    def _swap_queues(self):
        """
        Swaps the aggregation queues so we can aggregate the old queue safely
        Returns the old queue.
        """
        # Save the old queue
        old_queue = self.metrics_queue

        # Swap to the new queue
        new_queue = Queue.Queue()
        self.metrics_queue = new_queue

        # Return the old queue, there is no way writes will go through now
        return old_queue

    def _aggregate_queue(self, queue):
        # Sort the queue by the type of metric
        metric_types = {}
        while not queue.empty():
            metric = queue.get()
            metric_types.setdefault(type(metric),[])
            metric_types[type(metric)].append(metric)

        # Fold over the metrics by class
        data = []
        now = time.time()
        for cls in metric_types.keys():
            raw = metric_types[cls]
            aggregated = cls.fold(raw, now)
            data.extend(aggregated)

        return data

    def _flush_metrics(self, data):
        pass




