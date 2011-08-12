"""
This module implements the aggregator which is
used to collect statistics over a given time interval,
aggregate and then submit to Graphite.
"""
import logging
import time
import metrics

class Aggregator(object):
    def __init__(self, metrics_store, metrics_settings={}):
        """
        An aggregator accumulates metrics via the :meth:`add_metrics()` call
        until :meth:`flush()` is called. Flushing will be initiated in a new
        thread by the caller. Once flush is called, :meth:`add_metrics()` is
        guaranteed to never be called again. :meth:`flush()` is expected to
        send the aggregated metrics to the metrics store.

        Aggregators currently do not need to be thread safe. Only a single
        thread will call :meth:`add_metric()` at any given time.

        :Parameters:
            - `metrics_store`: The metrics storage instance to flush to.
        """
        self.metrics_store = metrics_store
        self.metrics_settings = self._load_metric_settings(metrics_settings)

    def add_metrics(self, metrics):
        """
        Add a collection of metrics to be aggregated in the next flushing
        period.
        """
        raise NotImplementedError()

    def flush(self):
        """
        This method will be called to run in a specific thread. It is responsible
        for flushing the collected metrics to the metrics store.
        """
        raise NotImplementedError()

    def _load_metric_settings(self, settings):
        """
        This method takes a list of settings set by the Statsite program,
        in the format of a dictionary keyed by the shorthand for the metric,
        example:

            { "ms": { "percentile": 80 } }

        And it turns it into a fast lookup based on the class that that
        setting actually represents:

            { Timer: { "percentile": 80 } }

        This format is much more efficient for ``_fold_metrics``.
        """
        result = {}
        for metric_type,metric_settings in settings.iteritems():
            result[metrics.METRIC_TYPES[metric_type]] = metric_settings

        return result

    def _fold_metrics(self, metrics):
        """
        This method will go over an array of metric objects and fold them into
        a list of data.
        """
        # Store the metrics as a dictionary by queue type
        metrics_by_type = {}
        for metric in metrics:
            key = type(metric)
            metrics_by_type.setdefault(key, [])
            metrics_by_type[key].append(metric)

        # Fold over the metrics
        data = []
        now = time.time()
        for cls,metrics in metrics_by_type.iteritems():
            data.extend(cls.fold(metrics, now, **self.metrics_settings.get(cls, {})))

        return data

class DefaultAggregator(Aggregator):
    def __init__(self, *args, **kwargs):
        super(DefaultAggregator, self).__init__(*args, **kwargs)

        self.metrics_queue = []
        self.logger = logging.getLogger("statsite.aggregator.default")

    def add_metrics(self, metrics):
        self.metrics_queue.extend(metrics)

    def flush(self):
        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug("Aggregating data...")

            for metric in self.metrics_queue:
                self.logger.debug("Metric: %s" % repr(metric))

        try:
            data = self._fold_metrics(self.metrics_queue)
        except:
            self.logger.exception("Failed to fold metrics data")

        try:
            if data:
                self.metrics_store.flush(data)
        except:
            self.logger.exception("Failed to flush data")

        self.logger.debug("Aggregation complete.")
